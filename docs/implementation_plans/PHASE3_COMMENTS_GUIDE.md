# Phase 3: Advanced Comment System - Implementation Guide

## ✅ What's Been Completed:

### 1. **Backend (Models, Views, URLs)**
- ✅ Updated Comment model with:
  - `parent` field for threaded replies
  - `updated_at` field to track edits
  - `is_edited` boolean flag
  - `is_reply` property

- ✅ Created new views:
  - `edit_comment()` - Edit your own comments
  - `delete_comment()` - Delete comments (author or post owner)
  - `reply_comment()` - Reply to comments

- ✅ Added URLs:
  - `/comment/<id>/edit/`
  - `/comment/<id>/delete/`
  - `/comment/<id>/reply/`

- ✅ Updated database table with new columns

### 2. **Features Implemented:**
- ✅ Edit your own comments
- ✅ Delete your own comments
- ✅ Post owner can delete any comment on their post
- ✅ Reply to comments (threaded/nested)
- ✅ Track edited comments with "(edited)" label

## 📝 What Needs to be Done (Frontend):

### Update `templates/community/feed.html`:

The comments section needs to be enhanced with:

1. **Edit/Delete Buttons** - Show for comment author
2. **Reply Button** - Show for all users
3. **Threaded Replies** - Display nested replies
4. **Edit Form** - Inline editing
5. **Reply Form** - Inline reply input

### JavaScript Functions Needed:

```javascript
// Edit comment
function editComment(commentId) {
    document.querySelector(`.comment-content-${commentId}`).style.display = 'none';
    document.querySelector(`.edit-form-${commentId}`).style.display = 'block';
}

function saveEdit(commentId) {
    const content = document.getElementById(`edit-input-${commentId}`).value;
    
    fetch(`/community/comment/${commentId}/edit/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: new FormData(Object.entries({content}).reduce((fd, [k, v]) => (fd.append(k, v), fd), new FormData()))
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}

function cancelEdit(commentId) {
    document.querySelector(`.comment-content-${commentId}`).style.display = 'block';
    document.querySelector(`.edit-form-${commentId}`).style.display = 'none';
}

// Delete comment
function deleteComment(commentId) {
    if (!confirm('Delete this comment?')) return;
    
    fetch(`/community/comment/${commentId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`comment-${commentId}`).remove();
        }
    });
}

// Reply to comment
function showReplyForm(commentId) {
    document.querySelector(`.reply-form-${commentId}`).style.display = 'block';
}

function submitReply(commentId) {
    const content = document.getElementById(`reply-input-${commentId}`).value;
    
    if (!content.trim()) return;
    
    const formData = new FormData();
    formData.append('content', content);
    
    fetch(`/community/comment/${commentId}/reply/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}
```

## 🎯 Quick Implementation Steps:

1. The backend is READY ✅
2. Database is UPDATED ✅
3. URLs are CONFIGURED ✅

**To complete:**
- Add the JavaScript functions above to the `<script>` section of feed.html
- Update the comment display to show edit/delete/reply buttons
- Add threaded reply display

## 🚀 Current Status:

**Backend:** 100% Complete ✅
**Frontend:** Needs JavaScript functions added
**Database:** 100% Complete ✅

The system is ready - just needs the frontend buttons and JavaScript to be fully functional!

## 📌 Key Features:

1. **Edit Comments** - Click pencil icon, edit inline, save
2. **Delete Comments** - Click trash icon (author or post owner)
3. **Reply to Comments** - Click "Reply", type response, nested display
4. **Edit Indicator** - Shows "(edited)" on modified comments
5. **Permissions** - Only author can edit, author/post owner can delete

All backend logic is in place and working!
