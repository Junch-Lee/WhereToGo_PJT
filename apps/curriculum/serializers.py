from rest_framework import serializers

from apps.accounts.models import Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = (
            "id",
            "name",
            "parent_topic",
            "depth",
            "topic_type",
            "is_learning_unit",
            "is_assessable",
            "description",
        )
