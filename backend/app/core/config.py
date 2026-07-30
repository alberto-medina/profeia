"""
Configuracion central del backend de ProfeIA.
Lee variables de entorno desde .env usando pydantic-settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    supabase_storage_bucket: str = "recursos-clases"

    # Proveedores de IA
    ia_contenido_api_key: str = ""
    ia_contenido_modelo: str = "gpt-4o-mini"
    ia_contenido_openai_url: str = "https://api.openai.com/v1/responses"
    ia_contenido_deepseek_api_key: str = ""
    ia_contenido_deepseek_modelo: str = "deepseek-chat"
    ia_contenido_deepseek_url: str = "https://api.deepseek.com/chat/completions"
    ia_contenido_openrouter_api_key: str = ""
    ia_contenido_openrouter_modelo: str = "deepseek/deepseek-chat"
    ia_contenido_openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    ia_contenido_groq_api_key: str = ""
    ia_contenido_groq_modelo: str = "llama-3.1-8b-instant"
    ia_contenido_groq_url: str = "https://api.groq.com/openai/v1/chat/completions"
    ia_contenido_fallback_local: bool = False
    ia_voz_api_key: str = ""
    ia_voz_proveedor: str = "openai"
    ia_voz_modelo: str = "gpt-4o-mini-tts"
    ia_voz_clonada_api_key: str = ""
    ia_voz_clonada_voice_id: str = ""
    ia_imagenes_api_key: str = ""
    ia_imagenes_modelo: str = "gpt-image-1"
    ia_imagenes_url: str = "https://api.openai.com/v1/images/generations"
    # Apagado porque la cuenta de OpenAI tiene el limite de facturacion
    # tocado (billing_hard_limit_reached). Mientras este asi, ni vale la
    # pena intentarlo: solo agrega espera y ruido de error en los logs
    # antes de caer a Hugging Face/Pollinations. Poner en True de nuevo
    # (o via env IA_IMAGENES_OPENAI_HABILITADO=true) una vez resuelto el
    # limite en platform.openai.com.
    ia_imagenes_openai_habilitado: bool = False
    ia_imagenes_secundario_api_key: str = ""
    ia_imagenes_secundario_modelo: str = ""
    ia_imagenes_secundario_url: str = ""
    ia_imagenes_huggingface_api_key: str = ""
    ia_imagenes_huggingface_modelo: str = "stabilityai/stable-diffusion-3-medium-diffusers"
    ia_video_api_key: str = ""

    # Mercado Pago
    mercado_pago_access_token: str = ""
    mercado_pago_webhook_secret: str = ""
    mercado_pago_back_url: str = "http://127.0.0.1:8000/pagos/mercadopago/retorno"

    # General
    entorno: str = "desarrollo"
    puerto: int = 8000
    backend_public_url: str = ""


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Devuelve una instancia cacheada de la configuracion."""
    return Configuracion()
