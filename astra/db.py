from sqlmodel import JSON, SQLModel, TypeDecorator, create_engine as _create_engine
from pydantic import parse_obj_as as _parse_obj_as
from pydantic.main import ModelMetaclass as _ModelMetaclass
from typing import TypeVar, Generic
from fastapi.encoders import jsonable_encoder as _jsonable_encoder
import json as json
import os

if os.environ.get("DB_URL") is None:
    raise Exception("DB_URL is empty!")

engine = _create_engine(os.environ.get("DB_URL"))


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


_T = TypeVar("_T")


def pydantic_column_type(pydantic_type):
    class PydanticJSONType(TypeDecorator, Generic[_T]):
        impl = JSON()

        def __init__(
            self,
            json_encoder=json,
        ):
            self.json_encoder = json_encoder
            super(PydanticJSONType, self).__init__()

        def bind_processor(self, dialect):
            impl_processor = self.impl.bind_processor(dialect)
            dumps = self.json_encoder.dumps
            if impl_processor:

                def process(value: _T):
                    if value is not None:
                        if isinstance(pydantic_type, _ModelMetaclass):
                            # This allows to assign non-InDB models and if they're
                            # compatible, they're directly parsed into the InDB
                            # representation, thus hiding the implementation in the
                            # background. However, the InDB model will still be returned
                            value_to_dump = pydantic_type.from_orm(value)
                        else:
                            value_to_dump = value
                        value = _jsonable_encoder(value_to_dump)
                    return impl_processor(value)

            else:

                def process(value):
                    if isinstance(pydantic_type, _ModelMetaclass):
                        # This allows to assign non-InDB models and if they're
                        # compatible, they're directly parsed into the InDB
                        # representation, thus hiding the implementation in the
                        # background. However, the InDB model will still be returned
                        value_to_dump = pydantic_type.from_orm(value)
                    else:
                        value_to_dump = value
                    value = dumps(_jsonable_encoder(value_to_dump))
                    return value

            return process

        def result_processor(self, dialect, coltype) -> _T:
            impl_processor = self.impl.result_processor(dialect, coltype)
            if impl_processor:

                def process(value):
                    value = impl_processor(value)
                    if value is None:
                        return None

                    data = value
                    # Explicitly use the generic directly, not type(T)
                    full_obj = _parse_obj_as(pydantic_type, data)
                    return full_obj

            else:

                def process(value):
                    if value is None:
                        return None

                    # Explicitly use the generic directly, not type(T)
                    full_obj = _parse_obj_as(pydantic_type, value)
                    return full_obj

            return process

        def compare_values(self, x, y):
            return x == y

    return PydanticJSONType
