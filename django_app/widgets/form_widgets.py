from django.forms.widgets import Widget


class VideoPlayer(Widget):
    """
    Base class for all <input> widgets.
    """
    template_name = 'widgets/video_player.html'

    def __init__(self, attrs=None):
        if attrs is not None:
            attrs = attrs.copy()
            self.input_type = attrs.pop('type', self.input_type)
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        return context