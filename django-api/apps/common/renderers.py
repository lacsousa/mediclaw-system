from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, dict) and {"data", "error"} <= set(data.keys()):
            return super().render(data, accepted_media_type, renderer_context)
        return super().render(
            {"data": data, "error": None, "meta": {}},
            accepted_media_type,
            renderer_context,
        )
