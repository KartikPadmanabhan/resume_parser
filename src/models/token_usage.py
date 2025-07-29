"""
Token usage tracking models for OpenAI API calls.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TokenUsage(BaseModel):
    """Token usage statistics for OpenAI API calls."""
    
    # Token counts
    input_tokens: int = Field(default=0, description="Number of input tokens")
    output_tokens: int = Field(default=0, description="Number of output tokens")
    cached_input_tokens: int = Field(default=0, description="Number of cached input tokens")
    total_tokens: int = Field(default=0, description="Total tokens used")
    
    # Cost calculations (per million tokens)
    input_cost_per_million: float = Field(default=2.50, description="Cost per million input tokens")
    cached_input_cost_per_million: float = Field(default=1.25, description="Cost per million cached input tokens")
    output_cost_per_million: float = Field(default=10.00, description="Cost per million output tokens")
    
    # Calculated costs
    input_cost: float = Field(default=0.0, description="Cost for input tokens")
    cached_input_cost: float = Field(default=0.0, description="Cost for cached input tokens")
    output_cost: float = Field(default=0.0, description="Cost for output tokens")
    total_cost: float = Field(default=0.0, description="Total cost for API call")
    
    # Metadata
    model_name: str = Field(default="gpt-4o", description="OpenAI model used")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of API call")
    
    def calculate_costs(self) -> None:
        """Calculate costs based on token usage and pricing."""
        # Calculate costs (pricing is per million tokens)
        self.input_cost = (self.input_tokens / 1_000_000) * self.input_cost_per_million
        self.cached_input_cost = (self.cached_input_tokens / 1_000_000) * self.cached_input_cost_per_million
        self.output_cost = (self.output_tokens / 1_000_000) * self.output_cost_per_million
        
        # Calculate total cost
        self.total_cost = self.input_cost + self.cached_input_cost + self.output_cost
        
        # Update total tokens
        self.total_tokens = self.input_tokens + self.cached_input_tokens + self.output_tokens
    
    def format_cost(self, cost: float) -> str:
        """Format cost as currency string."""
        return f"${cost:.6f}"
    
    def get_cost_breakdown(self) -> dict:
        """Get detailed cost breakdown."""
        return {
            "input_tokens": self.input_tokens,
            "input_cost": self.format_cost(self.input_cost),
            "cached_input_tokens": self.cached_input_tokens,
            "cached_input_cost": self.format_cost(self.cached_input_cost),
            "output_tokens": self.output_tokens,
            "output_cost": self.format_cost(self.output_cost),
            "total_tokens": self.total_tokens,
            "total_cost": self.format_cost(self.total_cost)
        }


class TokenTracker:
    """Utility class for tracking token usage across multiple API calls."""
    
    def __init__(self):
        self.usage_history: list[TokenUsage] = []
        self.current_session_usage: Optional[TokenUsage] = None
    
    def add_usage(self, usage: TokenUsage) -> None:
        """Add token usage to tracking history."""
        usage.calculate_costs()
        self.usage_history.append(usage)
        self.current_session_usage = usage
    
    def get_total_usage(self) -> TokenUsage:
        """Get cumulative token usage across all API calls."""
        if not self.usage_history:
            return TokenUsage()
        
        total_usage = TokenUsage()
        for usage in self.usage_history:
            total_usage.input_tokens += usage.input_tokens
            total_usage.output_tokens += usage.output_tokens
            total_usage.cached_input_tokens += usage.cached_input_tokens
            total_usage.input_cost += usage.input_cost
            total_usage.cached_input_cost += usage.cached_input_cost
            total_usage.output_cost += usage.output_cost
        
        total_usage.calculate_costs()
        return total_usage
    
    def get_current_usage(self) -> Optional[TokenUsage]:
        """Get token usage for the most recent API call."""
        return self.current_session_usage
    
    def reset_session(self) -> None:
        """Reset current session tracking."""
        self.current_session_usage = None
    
    def clear_history(self) -> None:
        """Clear all usage history."""
        self.usage_history.clear()
        self.current_session_usage = None
