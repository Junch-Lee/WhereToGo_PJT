from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers



User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
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