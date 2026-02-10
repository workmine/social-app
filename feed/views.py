from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Profile, Comment, Message  # <--- Message added here!
from .forms import UserRegisterForm, ProfileUpdateForm, PostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import JsonResponse
from django.db.models import Q

# --- AUTHENTICATION ---
def signup(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'feed/signup.html', {'form': form})

# --- MAIN FEED ---
@login_required
def home(request):
    Profile.objects.get_or_create(user=request.user)
    
    user_profile = request.user.profile
    following_users = user_profile.follows.all()
    posts = Post.objects.filter(
        user__profile__in=following_users
    ) | Post.objects.filter(user=request.user)
    posts = posts.distinct().order_by('-created_at')

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('home')
    else:
        form = PostForm()

    return render(request, 'feed/home.html', {'posts': posts, 'form': form})

# --- PROFILES ---
@login_required
def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile_obj, created = Profile.objects.get_or_create(user=user_obj)
    my_profile, created = Profile.objects.get_or_create(user=request.user)

    is_following = my_profile.follows.filter(user=user_obj).exists()
    user_posts = Post.objects.filter(user=user_obj).order_by('-created_at')

    return render(request, 'feed/profile.html', {
        'profile_user': user_obj, 
        'profile': profile_obj,
        'posts': user_posts, 
        'is_following': is_following,
        'followers_count': profile_obj.followed_by.count(),
        'following_count': profile_obj.follows.count()
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'feed/edit_profile.html', {'form': form})

# --- INTERACTIONS (LIKES & COMMENTS) ---
@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('home')

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        text = request.POST.get("text")
        if text:
            Comment.objects.create(user=request.user, post=post, text=text)
    return redirect('home')

# --- SEARCH ---
def search_users(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = User.objects.filter(username__icontains=query)
    return render(request, 'feed/search_results.html', {'results': results, 'query': query})

# --- CHAT SYSTEM ---
@login_required
def inbox(request):
    # Get all users involved in conversations with me
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    )
    users_messaged = set()
    for msg in messages:
        if msg.sender != request.user:
            users_messaged.add(msg.sender)
        else:
            users_messaged.add(msg.recipient)
            
    return render(request, 'feed/inbox.html', {'conversations': users_messaged})

@login_required
def direct_message(request, username):
    recipient = get_object_or_404(User, username=username)
    
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user))
    ).order_by('timestamp')

    if request.method == "POST":
        body = request.POST.get("body")
        file = request.FILES.get("file")  # Get the uploaded file
        
        # Only send if there is text OR a file
        if body or file:
            Message.objects.create(
                sender=request.user, 
                recipient=recipient, 
                body=body,
                file=file
            )
            return redirect('direct_message', username=username)

    return render(request, 'feed/chat.html', {'recipient': recipient, 'messages': messages})

# --- API (JSON) FOR JAVASCRIPT ---
@login_required
def like_post_api(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': post.total_likes()})

@login_required
def follow_user_api(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    my_profile = request.user.profile
    target_profile = user_to_follow.profile

    if my_profile.follows.filter(id=target_profile.id).exists():
        my_profile.follows.remove(target_profile)
        following = False
    else:
        my_profile.follows.add(target_profile)
        following = True
        
    return JsonResponse({'following': following, 'count': target_profile.followed_by.count()})

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # Security Check: Only allow delete if the user owns the post
    if request.user == post.user:
        post.delete()
    return redirect('home')