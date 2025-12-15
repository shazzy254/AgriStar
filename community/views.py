from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Post, PostImage, Comment, Follow, SavedPost, Report
from .forms import PostForm, CommentForm

User = get_user_model()

@login_required
def feed(request):
    """Main community feed"""
    # Get filter parameters
    category = request.GET.get('category')
    search = request.GET.get('search')
    filter_type = request.GET.get('filter', 'latest')
    
    # Base queryset
    posts = Post.objects.select_related('author', 'author__profile').prefetch_related(
        'images', 'likes', 'comments'
    )
    
    # Apply filters
    if category and category != 'ALL':
        posts = posts.filter(category=category)
    
    if search:
        posts = posts.filter(
            Q(content__icontains=search) | 
            Q(author__username__icontains=search) |
            Q(tags__icontains=search)
        )
    
    # Apply sorting
    if filter_type == 'following':
        # Show posts from people user follows
        following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
        posts = posts.filter(author__in=following_users)
    elif filter_type == 'popular':
        posts = posts.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')
    else:  # latest
        posts = posts.order_by('-created_at')
    
    # Pagination (20 posts per page)
    from django.core.paginator import Paginator
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    posts_page = paginator.get_page(page_number)
    
    # Logic for sidebar lists
    following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    
    # "Who to Follow" - exclude already followed and self
    suggested_users = User.objects.exclude(id__in=following_ids).exclude(id=request.user.id).order_by('?')[:5]
    
    # "Your Network" - recently followed
    following_list = User.objects.filter(id__in=following_ids).order_by('-id')[:5]

    context = {
        'posts': posts_page,
        'categories': Post.CATEGORY_CHOICES,
        'current_category': category,
        'current_filter': filter_type,
        'search_query': search,
        'suggested_users': suggested_users,
        'following_list': following_list,
    }
    return render(request, 'community/feed.html', context)


@login_required
def create_post(request):
    """Create a new post"""
    if request.method == 'POST':
        # Create a mutable copy of POST data
        post_data = request.POST.copy()
        
        # Remove images from form validation since we handle it separately
        form = PostForm(post_data)
        
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            # Ensure all fields have proper values to avoid NOT NULL constraints
            if not post.location or post.location.strip() == '':
                post.location = ''  # Use empty string instead of NULL
            
            # Ensure boolean fields have values
            if not hasattr(post, 'is_pest_alert') or post.is_pest_alert is None:
                post.is_pest_alert = False
            if not hasattr(post, 'is_flagged') or post.is_flagged is None:
                post.is_flagged = False
            
            # Ensure tags has a value
            if not hasattr(post, 'tags') or post.tags is None:
                post.tags = ''
            
            post.save()
            
            # Handle multiple images
            images = request.FILES.getlist('images')
            for image in images[:5]:  # Limit to 5 images
                PostImage.objects.create(post=post, image=image)
            
            messages.success(request, '🎉 Post created successfully!')
            return redirect('feed')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm()
    
    return render(request, 'community/create_post.html', {'form': form})


@login_required
def delete_post(request, post_id):
    """Delete a post"""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully.')
        return redirect('feed')
    
    return render(request, 'community/confirm_delete.html', {'post': post})


@login_required
def like_post(request, post_id):
    """Like/unlike a post (AJAX)"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': post.likes.count()
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        # Get content from form data
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        
        if content or image:
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                image=image
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'author': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%b %d, %Y %I:%M %p')
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
    
    return JsonResponse({'success': False}, status=400)


@login_required
def edit_comment(request, comment_id):
    """Edit a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Only author can edit their comment
    if comment.author != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            comment.content = content
            comment.is_edited = True
            comment.save()
            
            return JsonResponse({
                'success': True,
                'content': comment.content,
                'is_edited': True
            })
        else:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
    
    return JsonResponse({'success': False}, status=400)


@login_required
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Author can delete their comment, or post owner can delete any comment
    if comment.author != request.user and comment.post.author != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        comment.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)


@login_required
def reply_comment(request, comment_id):
    """Reply to a comment"""
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        
        if content or image:
            reply = Comment.objects.create(
                post=parent_comment.post,
                author=request.user,
                parent=parent_comment,
                content=content,
                image=image
            )
            
            return JsonResponse({
                'success': True,
                'reply': {
                    'id': reply.id,
                    'author': reply.author.username,
                    'content': reply.content,
                    'created_at': reply.created_at.strftime('%b %d, %Y %I:%M %p')
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Content or image is required'}, status=400)
    
    return JsonResponse({'success': False}, status=400)


@login_required
def like_comment(request, comment_id):
    """Like/unlike a comment (AJAX)"""
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': comment.likes_count
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def toggle_follow(request, user_id):
    """Follow/unfollow a user (AJAX)"""
    if request.method == 'POST':
        user_to_follow = get_object_or_404(User, id=user_id)
        
        if user_to_follow == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot follow yourself'}, status=400)
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if not created:
            follow.delete()
            following = False
        else:
            following = True
        
        return JsonResponse({
            'success': True,
            'following': following,
            'followers_count': user_to_follow.followers.count()
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def user_profile(request, user_id):
    """View a user's public profile"""
    profile_user = get_object_or_404(User, id=user_id)
    posts = Post.objects.filter(author=profile_user).prefetch_related('images', 'likes', 'comments')
    
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user, 
            following=profile_user
        ).exists()
    
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'followers_count': profile_user.followers.count(),
        'following_count': profile_user.following.count(),
        'is_own_profile': request.user == profile_user,
    }
    return render(request, 'community/user_profile.html', context)


@login_required
def toggle_save_post(request, post_id):
    """Save/unsave a post (AJAX)"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        saved_post, created = SavedPost.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if not created:
            saved_post.delete()
            saved = False
        else:
            saved = True
        
        return JsonResponse({
            'success': True,
            'saved': saved
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def saved_posts(request):
    """View user's saved posts"""
    saved = SavedPost.objects.filter(user=request.user).select_related('post__author').prefetch_related('post__images', 'post__likes')
    
    context = {
        'saved_posts': saved,
    }
    return render(request, 'community/saved_posts.html', context)


@login_required
def report_post(request, post_id):
    """Report a post"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        # Check if user already reported this post
        existing_report = Report.objects.filter(reporter=request.user, post=post).first()
        
        if existing_report:
            messages.warning(request, 'You have already reported this post.')
        else:
            Report.objects.create(
                reporter=request.user,
                post=post,
                reason=reason,
                description=description
            )
            messages.success(request, 'Thank you for your report. We will review it shortly.')
        
        return redirect('feed')
    
    context = {
        'post': post,
        'reasons': Report.REASON_CHOICES,
    }
    return render(request, 'community/report_post.html', context)

