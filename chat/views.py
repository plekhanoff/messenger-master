from rest_framework import viewsets
from .models import Chat, Message, UserProfile
from .serializers import ChatSerializer, MessageSerializer, UserProfileSerializer
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import SignUpForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.core.cache.backends.locmem import _caches as cache
from django.contrib.auth import logout
from .serializers import UserProfileSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import UserProfile
from .serializers import UserProfileSerializer
from .forms import UserProfileForm
from django.contrib.auth.models import User
from django.contrib import messages




 
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('profile')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('profile')

@login_required
def index(request):
    # Получаем все чаты пользователя
    user_chats = Chat.objects.filter(users=request.user).prefetch_related('users')
    
    # Разделяем чаты на групповые и приватные
    group_chats = user_chats.filter(is_group=True)
    private_chats = user_chats.filter(is_group=False)
    
    # Получаем список пользователей для создания новых приватных чатов
    available_users = User.objects.exclude(id=request.user.id)
    
    # Получаем последние сообщения для каждого чата
    for chat in user_chats:
        chat.last_message = Message.objects.filter(chat=chat).order_by('-timestamp').first()
    
    return render(request, 'chat/index.html', {
        'group_chats': group_chats,
        'private_chats': private_chats,
        'users': available_users,
        'user': request.user
    })

@login_required
def chat_room(request, room_name):
    try:
        chat = Chat.objects.get(name=room_name)
        if request.user not in chat.users.all():
            return redirect('index')
        
        chat_messages = Message.objects.filter(chat=chat).order_by('timestamp')
        # Получаем список пользователей, которых можно добавить в чат
        available_users = User.objects.exclude(
            id__in=chat.users.values_list('id', flat=True)
        ).exclude(id=request.user.id)
        
        return render(request, 'chat/chat_room.html', {
            'room_name': room_name,
            'chat_messages': chat_messages,
            'chat': chat,
            'available_users': available_users
        })
    except Chat.DoesNotExist:
        messages.error(request, f'Чат "{room_name}" не существует')
        return redirect('index')

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'chat/profile.html', {
        'form': form
    })

@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/user_list.html', {'users': users})

@login_required
def profile_view(request):
    return render(request, 'chat/profile.html', {
        'user': request.user
    })

@login_required
def create_chat(request):
    if request.method == 'POST':
        chat_name = request.POST.get('chat_name')
        try:
            # Проверяем, не существует ли чат с таким именем
            if Chat.objects.filter(name=chat_name).exists():
                messages.error(request, 'Чат с таким именем уже существует')
                return redirect('index')
            
            # Создаем новый чат
            chat = Chat.objects.create(
                name=chat_name,
                created_by=request.user,
                is_group=True
            )
            chat.users.add(request.user)
            messages.success(request, f'Чат "{chat_name}" успешно создан')
            return redirect('chat_room', room_name=chat_name)
        except Exception as e:
            messages.error(request, f'Ошибка при создании чата: {str(e)}')
            return redirect('index')
    return redirect('index')

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    
    def room_detail(request, room_name):
       room = Chat.objects.get(name=room_name)
       users_in_room = room.users.all() 
       context = {
           'room_name': room_name,
           'users_in_room': users_in_room
       }
       return render(request, 'chats.html', context)
   
   
        

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        queryset = Message.objects.all()

        chat_group_pk = self.kwargs.get('chat_group_pk')
        if chat_group_pk is not None:
            queryset = queryset.filter(chat_id=chat_group_pk)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, chat_id=self.kwargs['chat_group_pk'])
        

class UserProfileViewSet(viewsets.ModelViewSet): 
    queryset = UserProfile.objects.all() 
    serializer_class = UserProfileSerializer 

    def update_avatar(self, request):
        user = request.user  
        if request.method == 'POST':
            form = UserProfileForm(request.POST, request.FILES) 
            if form.is_valid():
                avatar = request.FILES.get('avatar/')  
                user.userprofile.avatar = avatar 
                user.userprofile.save() 
                return Response({"message": "Avatar updated successfully!"}, status=status.HTTP_200_OK)
            else:
                return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            form = UserProfileForm()
        
        return Response({'form': form}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def start_private_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Сначала создаем имя чата
    user_ids = sorted([request.user.id, other_user.id])
    chat_name = f'private_{user_ids[0]}_{user_ids[1]}'
    
    # Проверяем существование чата по имени
    existing_chat = Chat.objects.filter(name=chat_name).first()
    if existing_chat:
        # Если чат существует, пр��веряем права доступа
        if request.user in existing_chat.users.all():
            return redirect('chat_room', room_name=chat_name)
        else:
            messages.error(request, 'У вас нет доступа к этому чату')
            return redirect('index')
    
    # Если чат не существует, создаем новый
    try:
        chat = Chat.objects.create(
            name=chat_name,
            is_group=False,
            created_by=request.user
        )
        chat.users.add(request.user, other_user)
        messages.success(request, 'Приватный чат создан')
        return redirect('chat_room', room_name=chat_name)
    except Exception as e:
        messages.error(request, f'Ошибка при создании чата: {str(e)}')
        return redirect('index')
