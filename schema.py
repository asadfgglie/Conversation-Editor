import base64
import time

from pydantic import BaseModel, model_validator
from typing_extensions import Literal, Optional


class TextContent(BaseModel):
    type: Literal['text'] = 'text'
    text: str

    def __eq__(self, other):
        if not isinstance(other, TextContent):
            return False

        return self.text == other.text

    def __repr__(self):
        return super().__repr__().removeprefix(self.__class__.__name__).replace('(', '{').replace(')', '}')


class Image(BaseModel):
    url: str

    def __eq__(self, other):
        if not isinstance(other, Image):
            return False

        return self.url == other.url

    def __repr__(self):
        return super().__repr__().removeprefix(self.__class__.__name__).replace('(', '{').replace(')', '}')


class ImageContent(BaseModel):
    type: Literal['image_url'] = 'image_url'
    image_url: Image

    def __eq__(self, other):
        if not isinstance(other, ImageContent):
            return False

        return self.image_url == other.image_url

    def __repr__(self):
        return super().__repr__().removeprefix(self.__class__.__name__).replace('(', '{').replace(')', '}')

    def get_image_bytes(self) -> bytes:
        return base64.b64decode(self.image_url.url.removeprefix('data:image/jpeg;base64,'))


class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str | list[TextContent | ImageContent]

    name: Optional[str] = None
    """author name"""

    timestamp: str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    def get_text_content(self) -> str:
        if isinstance(self.content, str):
            return self.content
        else:
            return '\n'.join(c.text for c in self.content if isinstance(c, TextContent))

    def get_image_bytes_list(self) -> list[bytes]:
        tmp = []
        if isinstance(self.content, list):
            for m in self.content:
                if isinstance(m, ImageContent):
                    tmp.append(m.get_image_bytes())

        return tmp

    def __eq__(self, other):
        if not isinstance(other, Message):
            return False

        return (self.name == other.name and self.timestamp == other.timestamp
                and self.content == other.content and self.role == other.role)

    @model_validator(mode='after')
    def format(self):
        if self.name is None:
            self.name = self.role
        return self


class History(BaseModel):
    history: list[Message]

    def __repr__(self):
        return super().__repr__().removeprefix(self.__class__.__name__).replace('(', '{').replace(')', '}')