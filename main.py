import logging
import time
from datetime import datetime
from enum import Enum
from logging.config import dictConfig
from typing import List

import instructor
from config import Settings
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from security import authenticate_api_key
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
)

logger = logging.getLogger(__name__)


settings = Settings()

client = instructor.patch(OpenAI(api_key=settings.OPENAI_API_KEY))

app = FastAPI(title="Ticket Classification API", version="1.0.0")


# Adding CORS middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


app.add_middleware(TimingMiddleware)


# Initialize metrics

Instrumentator().instrument(app).expose(app)


# Enum for ticket types


class TicketCategory(str, Enum):
    ORDER_ISSUE = "order_issue"
    ACCOUNT_ACCESS = "account_access"
    PRODUCT_INQUIRY = "product_inquiry"
    TECHNICAL_SUPPORT = "technical_support"
    BILLING = "billing"
    OTHER = "other"


class CustomerSentiment(str, Enum):
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"


class TicketUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketClassification(BaseModel):
    category: TicketCategory
    urgency: TicketUrgency
    sentiment: CustomerSentiment
    confidence: float = Field(ge=0, le=1)
    key_information: List[str]
    suggested_action: str


class TicketRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)


# Classification logic
SYSTEM_PROMPT = """
You are an AI assistant for a large e-commerce platform's customer support team. 
Your role is to analyze incoming customer support tickets and provide structured information to help our team respond quickly and effectively.
Business Context:
- We handle thousands of tickets daily across various categories (orders, accounts, products, technical issues, billing).
- Quick and accurate classification is crucial for customer satisfaction and operational efficiency.
- We prioritize based on urgency and customer sentiment.
Your tasks:
1. Categorize the ticket into the most appropriate category.
2. Assess the urgency of the issue (low, medium, high, critical).
3. Determine the customer's sentiment.
4. Extract key information that would be helpful for our support team.
5. Suggest an initial action for handling the ticket.
6. Provide a confidence score for your classification.
Remember:
- Be objective and base your analysis solely on the information provided in the ticket.
- If you're unsure about any aspect, reflect that in your confidence score.
- For 'key_information', extract specific details like order numbers, product names, or account issues.
- The 'suggested_action' should be a brief, actionable step for our support team.
Analyze the following customer support ticket and provide the requested information in the specified format.
"""


def classify_ticket(ticket_text: str) -> TicketClassification:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=TicketClassification,
            temperature=0,
            max_retries=3,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {"role": "user", "content": ticket_text},
            ],
        )
        return response
    except Exception as e:
        logger.error(f"Error classifying ticket: {str(e)}")
        raise HTTPException(status_code=500, detail="Error classifying ticket")


#  API ENDPOINTS


@app.post("/classify_ticket", response_model=TicketClassification)
@limiter.limit("10/minute")
async def api_classify_ticket(
    request: Request,
    ticket: TicketRequest,
    api_key: str = Depends(authenticate_api_key),
):
    result = classify_ticket(ticket.text)
    logger.info(f"Ticket classified: {result.category}")
    return result


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Error handling

app.exception_handler(HTTPException)


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
