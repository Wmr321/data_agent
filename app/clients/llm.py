from langchain.chat_models import init_chat_model
from app.conf.app_config import app_config


class InitLlmClient:
    @staticmethod
    def init_text_model():
        return init_chat_model(
            model=app_config.llm.text_model,
            model_provider="openai",
            api_key=app_config.llm.api_key,
            base_url=app_config.llm.base_url,
            temperature= app_config.llm.text_model_temperature
        )

    @staticmethod
    def init_code_model():
        return init_chat_model(
            model=app_config.llm.code_model,
            model_provider="openai",
            api_key=app_config.llm.api_key,
            base_url=app_config.llm.base_url,
            temperature=app_config.llm.code_model_temperature
        )

text_model = InitLlmClient.init_text_model()
code_model = InitLlmClient.init_code_model()