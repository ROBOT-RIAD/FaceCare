from pydantic import BaseModel, Field


class RoutinePlan(BaseModel):

    morning: str = Field(
        description="Step by step morning skincare routine"
    )

    morning_product_ids: list[int] = Field(
        description="Database product IDs for morning routine"
    )

    night: str = Field(
        description="Step by step night skincare routine"
    )

    night_product_ids: list[int] = Field(
        description="Database product IDs for night routine"
    )

    precautions: list[str] = Field(
        default_factory=list,
        description="Important skincare precautions"
    )