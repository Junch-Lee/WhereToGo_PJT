from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Topic, UserInterestTopic, UserProfile



User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """
    POST /api/auth/signup/ 요청을 검증하고 User를 생성하는 serializer다.

    password_confirm은 DB에 저장하지 않는 검증 전용 필드이며, create 단계에서 제거한다.
    이메일 중복은 validate_email과 DB unique 제약 양쪽에서 방어한다.
    """

    password = serializers.CharField(
        write_only=True, # 요청에서는 받을 수 있지만, 응답에서는 절대 나가지 않도록 하는 설정
        min_length=8,
        error_messages={
            "min_length": "비밀번호는 8자 이상이어야 합니다.",
            "blank": "비밀번호를 입력해주세요.",
            "required": "비밀번호를 입력해주세요.",
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        error_messages={
            "blank": "비밀번호 확인을 입력해주세요.",
            "required": "비밀번호 확인을 입력해주세요."
        }
    )
    
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "password",
            "password_confirm",
            "agree_terms",
            "created_at",
        )
        read_only_fields = ("id", "created_at") # 클라이언트가 직접 보낼 수 없는 필드
        
        # 모델 기반으로 자동 생성된 필드에 추가 옵션을 붙이는 방식이다.
        # => email, nickname, agree_temrs 등 이미 User 모델에 있는 필드에 메시지나 조건 추가를 위해서 사용.
        extra_kwargs = {
            "email": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "이메일을 입력해주세요.",
                    "blank": "이메일을 입력해주세요.",
                    "invalid": "올바른 이메일 형식이 아닙니다."
                },
            },
            "nickname": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "닉네임을 입력해주세요.",
                    "blank": "닉네임을 입력해주세요.",
                    "max_length": "닉네임은 30자 이하로 입력해주세요."
                },
            },
            "agree_terms": {
                "required": True,
                "error_messages": {
                    "required": "약관 동의 여부가 필요합니다."
                },
            },            
        }
        
    def validate_email(self, value):
        email = User.objects.normalize_email(value).lower()
              
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")

        return email
    
    def validate_nickname(slef, value):
        nickname = value.strip()
        
        if not nickname:
            raise serializers.ValidationError("닉네임을 입력해주세요.")
        
        return nickname
    
    def validate_agree_terms(self, value):
       if value is not True:
           raise serializers.ValidationError("이용약관 및 개인정보 처리방침에 동의해야 합니다.")
       return value
    
    def validate(self, attrs):
        # attrs => 필드별 검증을 통과한 데이터 묶음이다.
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")
        
        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "비밀번호가 일치하지 않습니다."
            })
            
        validate_password(password)
        
        return attrs

    def create(self, validated_data):
        # validated_data => 모든 검증을 통과한 최종 데이터
        validated_data.pop("password_confirm") # DB에 저장할 값이 아니기 때문에 빼준다.
        password = validated_data.pop("password") # DB에 저장하긴 하지만 그대로 저장하면 안되기 때문에 별도로 전달해준다. => model에서 해싱해서 저장
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    password=password,
                    **validated_data
                )
                
        except IntegrityError:
            # IntegrityError => DB 제약조건 위반했을 때 발생하는 에러
            raise serializers.ValidationError({
                "email": "이미 가입된 이메일입니다."
            })
        
        return user
    

class LoginSerializer(serializers.Serializer):
    """
    POST /api/auth/login/ 요청을 검증하는 serializer다.

    authenticate를 통해 이메일/비밀번호를 확인하고, 비활성 계정이나 소프트 삭제 계정은
    토큰 발급 대상에서 제외한다. 실제 JWT 생성은 view에서 처리한다.
    """

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "이메일을 입력해주세요.",
            "blank": "이메일을 입력해주세요.",
            "invalid": "올바른 이메일 형식이 아닙니다."
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "blank": "비밀번호를 입력해주세요.",
        }
    )
    
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )
        
        if user is None:
            raise serializers.ValidationError({
                "non_field_errors": "이메일 또는 비밀번호가 올바르지 않습니다."
            })

        if not user.is_active or user.deleted_at is not None:
            raise serializers.ValidationError({
                "non_field_errors": "비활성화되었거나 탈퇴 처리된 계정입니다."
            })
            
        attrs["user"] = user
        return attrs


class UserMeSerializer(serializers.ModelSerializer):
    """
    GET/PATCH /api/users/me/ 응답과 수정 요청에 사용하는 serializer다.

    email은 로그인 식별자이므로 이 API에서는 수정하지 않고, nickname만 부분 수정할 수 있다.
    """

    class Meta:
        model = User
        fields = ("id", "email", "nickname", "created_at")
        read_only_fields = ("id", "email", "created_at")

    def validate_nickname(self, value):
        nickname = value.strip()

        if not nickname:
            raise serializers.ValidationError("nickname을 입력해주세요.")

        return nickname


class PasswordChangeSerializer(serializers.Serializer):
    """
    PATCH /api/users/me/password/ 요청을 검증하는 serializer다.

    현재 비밀번호가 맞는지 먼저 확인하고, 새 비밀번호와 확인값 일치 여부 및 Django 기본
    비밀번호 정책을 함께 검증한다.
    """

    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")

        return value

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                "new_password_confirm": "새 비밀번호가 일치하지 않습니다."
            })

        validate_password(new_password, self.context["request"].user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class UserProfileTopicSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 조회 응답에 포함되는 관심 토픽 표현용 serializer다.

    Topic 전체 모델 중 프로필 화면에서 관심 분야를 보여주는 데 필요한 필드를 그대로 내려준다.
    """

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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    GET/PATCH /api/users/me/profile/ 응답과 수정 요청에 사용하는 serializer다.

    interest_topics는 읽기 전용 중첩 응답이고, topic_ids는 관심 토픽 교체를 위한 쓰기 전용
    입력이다. preferred_learning_style은 커리큘럼 생성 요청에 값이 없을 때 fallback으로 쓰인다.
    """

    interest_topics = serializers.SerializerMethodField()
    topic_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = UserProfile
        fields = (
            "available_weekly_hours",
            "preferred_learning_style",
            "interest_topics",
            "topic_ids",
        )

    def get_interest_topics(self, obj):
        """
        사용자가 선택한 활성 관심 토픽만 id 오름차순으로 반환한다.

        비활성 토픽은 과거에 선택됐더라도 프로필 응답에서 제외해 화면과 추천 로직이 현재 사용
        가능한 토픽만 다루도록 한다.
        """
        topics = Topic.objects.filter(
            interested_users__user=obj.user,
            is_active=True,
        ).order_by("id")
        return UserProfileTopicSerializer(topics, many=True).data

    def validate_available_weekly_hours(self, value):
        if value < 0 or value > 168:
            raise serializers.ValidationError("주간 학습 가능 시간은 0 이상 168 이하로 입력해주세요.")

        return value

    def validate_topic_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        found_ids = set(
            Topic.objects.filter(id__in=unique_ids, is_active=True)
            .values_list("id", flat=True)
        )
        missing_ids = [topic_id for topic_id in unique_ids if topic_id not in found_ids]

        if missing_ids:
            raise serializers.ValidationError(
                f"존재하지 않는 topic id가 포함되어 있습니다: {missing_ids}"
            )

        return unique_ids

    def update(self, instance, validated_data):
        """
        프로필 기본 필드와 관심 토픽 목록을 함께 갱신한다.

        topic_ids가 전달된 경우 기존 관심 토픽을 삭제한 뒤 새 목록을 bulk_create한다. 부분 수정에서
        topic_ids가 생략되면 기존 관심 토픽은 그대로 유지된다.
        """
        topic_ids = validated_data.pop("topic_ids", None)
        instance = super().update(instance, validated_data)

        if topic_ids is not None:
            user = instance.user
            UserInterestTopic.objects.filter(user=user).delete()
            UserInterestTopic.objects.bulk_create(
                [
                    UserInterestTopic(user=user, topic_id=topic_id)
                    for topic_id in topic_ids
                ]
            )

        return instance
