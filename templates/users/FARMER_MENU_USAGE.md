# Farmer Hamburger Menu - Usage Guide

## How to Add the Menu to Any Page

The farmer hamburger menu is now a reusable component that can be added to any page where farmers need navigation.

### Step 1: Include the Menu Component

Add this line right after `{% block content %}` in any farmer-facing template:

```html
{% block content %}
<!-- Include Farmer Menu -->
{% include 'users/farmer_menu.html' %}

<!-- Your page content here -->
<div class="your-content">
    ...
</div>
{% endblock %}
```

### Step 2: That's It!

The menu will automatically:
- ✅ Show the hamburger button in the top-left corner
- ✅ Display the farmer's username and profile
- ✅ Highlight the active page
- ✅ Include all navigation links:
  - Dashboard
  - My Profile
  - Marketplace
  - Calendar
  - AI Assistant
  - Community

### Example Usage

**In `profile_display.html`:**
```html
{% extends 'base.html' %}

{% block content %}
{% include 'users/farmer_menu.html' %}

<div class="container mt-4">
    <h2>My Profile</h2>
    <!-- Profile content -->
</div>
{% endblock %}
```

**In `calendar.html`:**
```html
{% extends 'base.html' %}

{% block content %}
{% include 'users/farmer_menu.html' %}

<div class="container mt-4">
    <h2>My Calendar</h2>
    <!-- Calendar content -->
</div>
{% endblock %}
```

### Features

- **Responsive**: Works on all devices
- **Auto-active**: Automatically highlights the current page
- **Smooth animations**: Slides in/out beautifully
- **Click to close**: Tap overlay or X to close menu
- **Auto-close on link click**: Menu closes when you select a page

### Menu Links Included

1. **Dashboard** - Main farmer dashboard
2. **My Profile** - Profile management & product management
3. **Marketplace** - Browse and sell products
4. **Calendar** - Farm calendar and journal
5. **AI Assistant** - AI farming assistant
6. **Community** - Community feed

---

**Note**: The menu is styled with agriculture theme colors (greens, gold) and matches the overall AgriStar design.
