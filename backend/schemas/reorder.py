from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from ..models.reorder import ReorderRequest, ReorderItem


class ReorderRequestSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ReorderRequest
        load_instance = True


class ReorderItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ReorderItem
        load_instance = True
