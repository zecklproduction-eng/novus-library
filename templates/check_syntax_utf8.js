{% extends "base.html" %}

{% block title %}{{ group.name if group else 'Group' }} | NOVUS Community{% endblock %}

{% block content %}



    .group-page,
    .group-page * {
        font-family: 'Inter', sans-serif;
    }


        Back to Community

                    {% if group and group.icon_url %}
                    {% else %}
                    {% endif %}
                            {{ group.member_count if group else '1,234' }} members
                            {{ group.post_count if group else '456' }} posts
                            Created {{ group.created_at if group else 'Jan 2024' }}



                    {{ group.description if group else 'Welcome to Global Club! A community for manga and anime
                    enthusiasts to share their passion, discuss their favorite series, and connect with like-minded fans
                    from around the world.' }}

                    {% if admins %}
                    {% for admin in admins %}
                    {% endfor %}
                    {% else %}
                    {% endif %}


                    {% if can_edit_settings %}
                    {% endif %}
                    {% if channels %}
                    {% for channel in channels %}
                    {% endfor %}
                    {% else %}
                    {% endif %}






                                            Select an award to give to this post

                                Post







                {% if posts %}
                {% for post in posts %}


                        {% if post.title %}
                        {% endif %}


                        {% if post.post_type == 'poll' and post.poll %}
                                {% set total_votes = 0 %}
                                {% for opt in post.poll.options %}
                                {% set total_votes = total_votes + opt.votes %}
                                {% endfor %}

                                {% for opt in post.poll.options %}
                                {% set is_voted = opt.id in post.poll.user_votes %}
                                    class="poll-option-btn {{ 'voted' if post.poll.user_votes else '' }} {{ 'selected' if is_voted else '' }}"
                                    onclick="togglePollOption({{ post.poll.id }}, {{ opt.id }}, {{ 'true' if post.poll.allow_multiple else 'false' }})"
                                        {% if post.poll.user_votes %}
                                        {% endif %}
                                {% endfor %}
                                {% if not post.poll.user_votes %}
                                {% else %}
                                {% endif %}
                        {% endif %}

                        {% if post.attachments %}
                            {% for attach in post.attachments %}
                            {% if attach.type in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'sticker'] %}
                            {% elif attach.type == 'manga_link' %}
                                {% if attach.manga_cover %}
                                {% else %}
                                {% endif %}
                            {% else %}
                            {% endif %}
                            {% endfor %}
                        {% endif %}


                            {% if post.user_id == session.get('user_id') or session.get('role') == 'admin' %}
                                    onclick="editPost({{ post.id }}, '{{ post.content|replace("'", "\\'") }}')"
                            {% endif %}


                                            onfocus="window.activeInput=this; window.activePickerPostId={{ post.id }};"
                                                Reply
                {% endfor %}
                {% else %}
                {% endif %}





                    {% if recent_members %}
                    {% for member in recent_members %}
                    {% endfor %}
                    {% else %}
                    {% endif %}

                    {% if related_groups %}
                    {% for rg in related_groups %}
                            {% if rg.group_type == 'genre' %}
                            {% elif rg.group_type == 'manga' %}
                            {% elif rg.group_type == 'book' %}
                            {% else %}
                            {% endif %}
                    {% endfor %}
                    {% else %}
                    {% endif %}












                                {% if group and group.icon_url %}
                                {% else %}
                                {% endif %}

                                {% if group and group.banner_url %}
                                {% else %}
                                {% endif %}








                            {% if admins %}
                            {% for admin in admins %}
                            {% endfor %}
                            {% else %}
                            {% endif %}















    /* Modal Overlay */
    .settings-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }

    .settings-modal-overlay.active {
        opacity: 1;
        visibility: visible;
    }

    /* Modal Container */
    .settings-modal {
        background: linear-gradient(145deg, rgba(30, 35, 55, 0.98), rgba(20, 25, 40, 0.98));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        width: 90%;
        max-width: 900px;
        max-height: 85vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 188, 212, 0.1);
        transform: scale(0.9) translateY(20px);
        transition: transform 0.3s ease;
    }

    .settings-modal-overlay.active .settings-modal {
        transform: scale(1) translateY(0);
    }

    /* Modal Header */
    .settings-modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .settings-modal-header h2 {
        font-size: 20px;
        font-weight: 600;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0;
    }

    .settings-modal-header h2 svg {
        width: 22px;
        height: 22px;
        color: #00bcd4;
    }

    .settings-close-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 8px;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.6);
        transition: all 0.2s ease;
    }

    .settings-close-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
    }

    /* Modal Body */
    .settings-modal-body {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    /* Settings Sidebar */
    .settings-sidebar {
        width: 220px;
        background: rgba(0, 0, 0, 0.2);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
        padding: 16px 12px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .settings-nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: transparent;
        border: none;
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
    }

    .settings-nav-item svg {
        width: 18px;
        height: 18px;
    }

    .settings-nav-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #fff;
    }

    .settings-nav-item.active {
        background: linear-gradient(135deg, rgba(0, 188, 212, 0.2), rgba(0, 150, 170, 0.15));
        color: #00bcd4;
    }

    .settings-nav-item.danger {
        color: rgba(231, 76, 60, 0.8);
    }

    .settings-nav-item.danger:hover,
    .settings-nav-item.danger.active {
        background: rgba(231, 76, 60, 0.15);
        color: #e74c3c;
    }

    /* Settings Content */
    .settings-content {
        flex: 1;
        padding: 24px 32px;
        overflow-y: auto;
    }

    .settings-tab-content {
        display: none;
    }

    .settings-tab-content.active {
        display: block;
    }

    .settings-tab-content h3 {
        font-size: 18px;
        font-weight: 600;
        color: #fff;
        margin: 0 0 4px 0;
    }

    .settings-description {
        color: rgba(255, 255, 255, 0.5);
        font-size: 13px;
        margin: 0 0 24px 0;
    }

    /* Form Groups */
    .settings-form-group {
        margin-bottom: 24px;
    }

    .settings-form-group label {
        display: block;
        font-size: 13px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
        margin-bottom: 8px;
    }

    .settings-input,
    .settings-textarea,
    .settings-select {
        width: 100%;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 12px 16px;
        color: #fff;
        font-size: 14px;
        transition: all 0.2s ease;
    }

    .settings-input:focus,
    .settings-textarea:focus,
    .settings-select:focus {
        outline: none;
        border-color: rgba(0, 188, 212, 0.5);
        box-shadow: 0 0 0 3px rgba(0, 188, 212, 0.1);
    }

    .settings-textarea {
        resize: vertical;
        min-height: 100px;
    }

    /* Image Upload */
    .settings-image-upload {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .image-preview {
        width: 80px;
        height: 80px;
        background: rgba(0, 0, 0, 0.3);
        border: 2px dashed rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .image-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .image-preview svg {
        width: 32px;
        height: 32px;
        color: rgba(255, 255, 255, 0.3);
    }

    .banner-preview {
        width: 200px;
        height: 60px;
        border-radius: 8px;
    }

    .upload-controls {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .btn-upload {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        background: rgba(0, 188, 212, 0.15);
        border: 1px solid rgba(0, 188, 212, 0.3);
        border-radius: 8px;
        color: #00bcd4;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-upload:hover {
        background: rgba(0, 188, 212, 0.25);
    }

    .btn-upload svg {
        width: 16px;
        height: 16px;
    }

    .upload-hint {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
    }

    /* Color Picker */
    .color-picker-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .settings-color-picker {
        width: 50px;
        height: 40px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
    }

    .color-hex {
        font-family: monospace;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.7);
    }

    /* Radio Groups */
    .settings-radio-group {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .settings-radio {
        cursor: pointer;
    }

    .settings-radio input {
        display: none;
    }

    .radio-label {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px;
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        transition: all 0.2s ease;
    }

    .settings-radio input:checked+.radio-label {
        background: rgba(0, 188, 212, 0.1);
        border-color: rgba(0, 188, 212, 0.3);
    }

    .radio-label svg {
        width: 20px;
        height: 20px;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 2px;
    }

    .settings-radio input:checked+.radio-label svg {
        color: #00bcd4;
    }

    .radio-label strong {
        display: block;
        color: #fff;
        font-size: 14px;
        margin-bottom: 2px;
    }

    .radio-label p {
        margin: 0;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
    }

    /* Advanced Posting Features */
    .create-post-extras {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .post-extra-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .post-extra-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
    }

    .post-extra-btn svg {
        width: 16px;
        height: 16px;
    }

    .attachment-previews {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
    }

    .attachment-preview {
        position: relative;
        width: 60px;
        height: 60px;
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .attachment-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .attachment-preview .remove-attach {
        position: absolute;
        top: 2px;
        right: 2px;
        width: 16px;
        height: 16px;
        background: rgba(0, 0, 0, 0.6);
        border-radius: 4px;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 10px;
    }

    /* Post Rendering Attachments */
    .post-attachments {
        margin-top: 12px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .post-attachment-img {
        max-width: 100%;
        max-height: 400px;
        border-radius: 8px;
        cursor: pointer;
    }

    .post-attachment-file {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 16px;
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #fff;
        text-decoration: none;
        font-size: 13px;
    }

    .post-attachment-manga {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: rgba(0, 188, 212, 0.05);
        border: 1px solid rgba(0, 188, 212, 0.2);
        border-radius: 10px;
        width: 100%;
        max-width: 400px;
        text-decoration: none;
        transition: transform 0.2s ease;
    }

    .post-attachment-manga:hover {
        transform: translateY(-2px);
        background: rgba(0, 188, 212, 0.1);
    }

    .manga-link-cover,
    .manga-preview-img {
        width: 60px;
        height: 84px;
        border-radius: 8px;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .manga-link-info h4 {
        margin: 0;
        color: #00bcd4;
        font-size: 14px;
    }

    .manga-link-info p {
        margin: 4px 0 0;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
    }

    /* Comment Section */
    .post-comments-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        display: none;
    }

    .comment-list {
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin-bottom: 20px;
    }

    .comment-item {
        display: flex;
        gap: 12px;
    }

    .comment-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
    }

    .comment-content-wrap {
        flex: 1;
        background: rgba(255, 255, 255, 0.03);
        padding: 10px 14px;
        border-radius: 10px;
    }

    .comment-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }

    .comment-user {
        font-weight: 600;
        font-size: 13px;
        color: #fff;
    }

    .comment-time {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
    }

    .comment-body {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.8);
        line-height: 1.5;
    }

    .comment-input-wrap {
        display: flex;
        gap: 12px;
        align-items: flex-start;
    }

    .comment-input {
        flex: 1;
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px 14px;
        color: #fff;
        font-size: 13px;
        outline: none;
        resize: none;
        min-height: 40px;
    }

    /* Manga Search Popup */
    .manga-search-popup {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: linear-gradient(145deg, #1e2333, #151820);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        z-index: 1000;
        display: none;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6);
        overflow: hidden;
    }

    .manga-search-popup.active {
        display: block;
    }

    .manga-search-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(0, 188, 212, 0.05);
    }

    .manga-search-header h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .manga-search-header h4 svg {
        width: 16px;
        height: 16px;
        color: #00bcd4;
    }

    .manga-popup-close {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.5);
        font-size: 20px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
    }

    .manga-popup-close:hover {
        color: #fff;
    }

    .manga-search-input-wrap {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .manga-search-input-wrap svg {
        width: 16px;
        height: 16px;
        color: rgba(255, 255, 255, 0.3);
    }

    .manga-search-input-wrap input {
        flex: 1;
        background: transparent;
        border: none;
        color: #fff;
        font-size: 14px;
        outline: none;
    }

    .manga-search-input-wrap input::placeholder {
        color: rgba(255, 255, 255, 0.3);
    }

    .manga-search-results {
        max-height: 280px;
        overflow-y: auto;
    }

    .manga-search-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        cursor: pointer;
        transition: background 0.2s;
    }

    .manga-search-item:hover {
        background: rgba(0, 188, 212, 0.1);
    }

    .manga-search-item img {
        width: 40px;
        min-width: 40px;
        height: 56px;
        border-radius: 4px;
        object-fit: cover;
        background: rgba(0, 0, 0, 0.3);
    }

    .manga-search-details h5 {
        margin: 0;
        font-size: 13px;
        color: #fff;
    }

    .manga-search-details p {
        margin: 0;
        font-size: 10px;
        color: rgba(255, 255, 255, 0.4);
    }

    /* Comment Section Enhancements */
    .comment-input-container {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .comment-input-box {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        overflow: hidden;
    }

    .comment-input {
        background: transparent;
        border: none;
        width: 100%;
        padding: 10px 12px;
        color: #fff;
        resize: none;
        font-size: 13px;
        outline: none;
        margin: 0;
    }

    .comment-input-actions {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .comment-extra-btns {
        display: flex;
        gap: 4px;
    }

    .comment-extra-btn {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.4);
        padding: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .comment-extra-btn:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #00bcd4;
    }

    .comment-extra-btn svg {
        width: 14px;
        height: 14px;
    }

    .comment-previews {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .attachment-preview.mini {
        width: 40px;
        height: 40px;
        border-radius: 4px;
    }

    .attachment-preview.mini img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .attachment-preview.mini .remove-attach {
        width: 14px;
        height: 14px;
        font-size: 10px;
        top: -5px;
        right: -5px;
    }

    /* Comment Item Enhancements */
    .comment-attachments {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
    }

    .comment-attachment-img {
        max-width: 150px;
        max-height: 150px;
        border-radius: 6px;
        cursor: pointer;
        transition: opacity 0.2s;
    }

    .comment-attachment-img:hover {
        opacity: 0.9;
    }

    /* Interactive Pickers CSS */
    .picker-popover {
        position: absolute;
        bottom: 100%;
        left: 0;
        width: 300px;
        background: #1e2333;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: none;
        flex-direction: column;
        overflow: hidden;
        margin-bottom: 10px;
    }

    .picker-popover.active {
        display: flex;
        animation: slideUpFade 0.2s ease-out;
    }

    @keyframes slideUpFade {
        from {
            opacity: 0;
            transform: translateY(10px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .picker-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.03);
    }

    .picker-header h4 {
        margin: 0;
        font-size: 13px;
        font-weight: 600;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .picker-close {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        padding: 4px;
        display: flex;
    }

    .picker-close:hover {
        color: #fff;
    }

    .emoji-grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 4px;
        padding: 10px;
        max-height: 250px;
        overflow-y: auto;
    }

    .emoji-item {
        font-size: 20px;
        padding: 5px;
        cursor: pointer;
        text-align: center;
        border-radius: 4px;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .emoji-item:hover {
        background: rgba(0, 188, 212, 0.2);
    }

    .gif-search-wrap {
        padding: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .gif-search-input {
        width: 100%;
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 8px 10px;
        color: #fff;
        font-size: 13px;
        outline: none;
    }

    .gif-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        padding: 10px;
        max-height: 250px;
        overflow-y: auto;
    }

    .gif-item {
        width: 100%;
        height: 80px;
        object-fit: cover;
        border-radius: 4px;
        cursor: pointer;
        transition: transform 0.2s;
    }

    .gif-item:hover {
        transform: scale(1.05);
    }

    /* Poll Styling */
    .poll-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-top: 12px;
    }

    .poll-question {
        font-size: 15px;
        font-weight: 600;
        color: #fff;
        margin-bottom: 16px;
    }

    .poll-options {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .poll-option-btn {
        position: relative;
        width: 100%;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #fff;
        text-align: left;
        cursor: pointer;
        overflow: hidden;
        transition: all 0.2s ease;
    }

    .poll-option-btn:hover:not(.voted) {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(0, 188, 212, 0.3);
    }

    .poll-option-btn.selected {
        border-color: #00bcd4;
        background: rgba(0, 188, 212, 0.1);
    }

    .poll-progress-bar {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: rgba(0, 188, 212, 0.2);
        z-index: 1;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .poll-option-content {
        position: relative;
        z-index: 2;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;
    }

    .poll-vote-pct {
        font-weight: 700;
        color: #00bcd4;
    }

    .poll-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
    }

    .vote-submit-btn {
        background: #00bcd4;
        color: #000;
        border: none;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }

    .vote-submit-btn:disabled {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.3);
        cursor: not-allowed;
    }

    opacity: 0.8;
    }

    .comment-attachment-file {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        color: #fff;
        text-decoration: none;
        font-size: 12px;
    }

    .comment-attachment-file svg {
        width: 14px;
        height: 14px;
        color: #00bcd4;
    }

    .comment-actions {
        display: flex;
        gap: 12px;
        margin-top: 6px;
    }

    .comment-like-btn {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.4);
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        cursor: pointer;
        padding: 2px 4px;
        border-radius: 4px;
        transition: all 0.2s;
    }

    .comment-like-btn:hover {
        color: #ff4757;
        background: rgba(255, 71, 87, 0.1);
    }

    .comment-like-btn.active {
        color: #ff4757;
    }

    /* Post Owner Actions (Edit/Delete) */
    .post-owner-actions {
        display: flex;
        gap: 4px;
        margin-left: auto;
    }

    .post-edit-btn,
    .post-delete-btn {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.4);
        padding: 6px;
        cursor: pointer;
        border-radius: 6px;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .post-edit-btn svg,
    .post-delete-btn svg {
        width: 16px;
        height: 16px;
    }

    .post-edit-btn:hover {
        background: rgba(0, 188, 212, 0.1);
        color: #00bcd4;
    }

    .post-delete-btn:hover {
        background: rgba(255, 71, 87, 0.1);
        color: #ff4757;
    }

    /* Edit Post Modal */
    .edit-post-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        z-index: 2000;
        display: none;
        align-items: center;
        justify-content: center;
    }

    .edit-post-modal.active {
        display: flex;
    }

    .edit-post-dialog {
        background: linear-gradient(145deg, #1e2333, #151820);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        width: 500px;
        max-width: 90vw;
    }

    .edit-post-dialog h3 {
        color: #fff;
        margin: 0 0 15px;
        font-size: 16px;
    }

    .edit-post-dialog textarea {
        width: 100%;
        min-height: 120px;
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #fff;
        padding: 12px;
        font-size: 14px;
        resize: vertical;
        outline: none;
    }

    .edit-post-actions {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
        margin-top: 15px;
    }

    .edit-post-cancel {
        background: rgba(255, 255, 255, 0.1);
        border: none;
        color: #fff;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
    }

    .edit-post-save {
        background: linear-gradient(135deg, #00bcd4, #00acc1);
        border: none;
        color: #fff;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
    }

    .spin {
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        from {
            transform: rotate(0deg);
        }

        to {
            transform: rotate(360deg);
        }
    }

    /* Channels Section Styles */
    .group-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }

    .add-channel-btn {
        background: rgba(0, 188, 212, 0.1);
        border: none;
        color: #00bcd4;
        width: 24px;
        height: 24px;
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .add-channel-btn:hover {
        background: rgba(0, 188, 212, 0.2);
    }

    .add-channel-btn svg {
        width: 14px;
        height: 14px;
    }

    .channels-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .channel-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 6px;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.6);
        transition: all 0.2s;
    }

    .channel-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #fff;
    }

    .channel-item.active {
        background: rgba(0, 188, 212, 0.1);
        color: #00bcd4;
    }

    .channel-item svg {
        width: 16px;
        height: 16px;
    }

    .channel-item span {
        font-size: 13px;
    }

    /* Mention Dropdown Styles */
    .mention-dropdown {
        position: absolute;
        bottom: 100%;
        left: 0;
        right: 0;
        background: linear-gradient(145deg, #1e2333, #151820);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        max-height: 250px;
        overflow-y: auto;
        display: none;
        z-index: 1000;
        box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 8px;
    }

    .mention-dropdown.active {
        display: block;
    }

    .mention-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        cursor: pointer;
        transition: background 0.2s;
    }

    .mention-item:hover {
        background: rgba(0, 188, 212, 0.1);
    }

    .mention-item img {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
    }

    .mention-item .mention-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00bcd4, #00acc1);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .mention-item .mention-icon svg {
        width: 16px;
        height: 16px;
        color: #fff;
    }

    .mention-info {
        flex: 1;
    }

    .mention-username {
        font-size: 13px;
        font-weight: 600;
        color: #fff;
    }

    .mention-username.special {
        color: #00bcd4;
    }

    .mention-username.role {
        color: #ff9800;
    }

    .mention-desc {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
    }

    .mention-badge {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(0, 188, 212, 0.2);
        color: #00bcd4;
    }

    /* Style for mentions in text */
    .mention-tag {
        color: #00bcd4;
        font-weight: 600;
        background: rgba(0, 188, 212, 0.1);
        padding: 0 4px;
        border-radius: 3px;
        cursor: pointer;
    }

    .mention-tag.role-mention {
        color: #ff9800;
        background: rgba(255, 152, 0, 0.1);
    }

    .mention-tag.mod-mention {
        color: #e91e63;
        background: rgba(233, 30, 99, 0.1);
    }

    /* Poll CSS */
    .poll-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    }

    .poll-question {
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 12px;
        color: #fff;
    }

    .poll-options {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .poll-option-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 10px 14px;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s;
        position: relative;
        overflow: hidden;
        color: rgba(255, 255, 255, 0.8);
        font-size: 14px;
    }

    .poll-option-btn:hover:not(.voted) {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .poll-option-btn.selected {
        border-color: #00bcd4;
        background: rgba(0, 188, 212, 0.1);
    }

    .poll-option-btn.voted {
        cursor: default;
    }

    .poll-progress-bar {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        background: rgba(0, 188, 212, 0.15);
        z-index: 0;
        transition: width 0.6s cubic-bezier(0.1, 0, 0, 1);
    }

    .poll-option-content {
        position: relative;
        z-index: 1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .poll-vote-pct {
        font-weight: 600;
        font-size: 12px;
        color: #00bcd4;
    }

    .poll-footer {
        margin-top: 12px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.4);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .vote-submit-btn {
        background: #00bcd4;
        color: #fff;
        border: none;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: 0.2s;
    }

    .vote-submit-btn:hover {
        background: #00acc1;
    }

    .vote-submit-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .mention-tag.user-mention {
        color: #00bcd4;
    }

    .post-input-wrapper {
        display: flex;
        gap: 12px;
        align-items: flex-start;
        margin-bottom: 12px;
    }

    .post-input-main {
        flex: 1;
        background: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        overflow: hidden;
        transition: border-color 0.3s;
    }

    .post-input-main:focus-within {
        border-color: #00bcd4;
    }

    .create-post-textarea {
        width: 100%;
        min-height: 80px;
        background: transparent;
        border: none;
        color: #fff;
        padding: 12px;
        font-size: 14px;
        resize: vertical;
        outline: none;
    }

    .post-input-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        background: rgba(0, 0, 0, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .post-input-actions-left {
        display: flex;
        gap: 8px;
    }

    .post-action-icon {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .post-action-icon:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
    }

    .post-action-icon svg {
        width: 18px;
        height: 18px;
    }

    /* Input Action Divider */
    .input-actions-divider {
        width: 1px;
        height: 20px;
        background: rgba(255, 255, 255, 0.1);
        margin: 0 4px;
        align-self: center;
    }

    .comment-extra-btn {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .comment-extra-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
    }

    .comment-extra-btn svg {
        width: 20px;
        height: 20px;
    }

    @keyframes spin {
        from {
            transform: rotate(0deg);
        }

        to {
            transform: rotate(360deg);
        }
    }

    /* Toggle Switch */
    .settings-toggle-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    .settings-toggle-row span {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.8);
    }

    .settings-toggle {
        position: relative;
        width: 48px;
        height: 26px;
    }

    .settings-toggle input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 26px;
        transition: 0.3s;
    }

    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 20px;
        width: 20px;
        left: 3px;
        bottom: 3px;
        background: #fff;
        border-radius: 50%;
        transition: 0.3s;
    }

    .settings-toggle input:checked+.toggle-slider {
        background: linear-gradient(135deg, #00bcd4, #0097a7);
    }

    .settings-toggle input:checked+.toggle-slider:before {
        transform: translateX(22px);
    }

    /* Member Management */
    .member-management-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .member-management-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
    }

    .member-management-item img {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
    }

    .member-management-item .member-info {
        flex: 1;
    }

    .member-management-item .member-name {
        display: block;
        font-size: 14px;
        color: #fff;
    }

    .member-management-item .member-role {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
    }

    .role-select {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        padding: 6px 10px;
        color: #fff;
        font-size: 12px;
    }

    .add-admin-row {
        display: flex;
        gap: 8px;
    }

    .add-admin-row .settings-input {
        flex: 1;
    }

    .btn-add-admin {
        padding: 12px 16px;
        background: rgba(0, 188, 212, 0.15);
        border: 1px solid rgba(0, 188, 212, 0.3);
        border-radius: 8px;
        color: #00bcd4;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-add-admin:hover {
        background: rgba(0, 188, 212, 0.25);
    }

    .banned-list-empty {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 20px;
        background: rgba(46, 204, 113, 0.1);
        border-radius: 10px;
        color: #2ecc71;
        font-size: 14px;
    }

    .banned-list-empty svg {
        width: 20px;
        height: 20px;
    }

    /* Danger Zone */
    .danger-zone-card {
        background: rgba(231, 76, 60, 0.05);
        border: 1px solid rgba(231, 76, 60, 0.2);
        border-radius: 12px;
        overflow: hidden;
    }

    .danger-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid rgba(231, 76, 60, 0.1);
    }

    .danger-item:last-child {
        border-bottom: none;
    }

    .danger-item.critical {
        background: rgba(231, 76, 60, 0.1);
    }

    .danger-info strong {
        display: block;
        color: #fff;
        font-size: 14px;
        margin-bottom: 4px;
    }

    .danger-info p {
        margin: 0;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
    }

    .btn-danger-secondary {
        padding: 8px 16px;
        background: transparent;
        border: 1px solid rgba(231, 76, 60, 0.5);
        border-radius: 6px;
        color: #e74c3c;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-danger-secondary:hover {
        background: rgba(231, 76, 60, 0.1);
    }

    .btn-danger {
        padding: 8px 16px;
        background: #e74c3c;
        border: none;
        border-radius: 6px;
        color: #fff;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-danger:hover {
        background: #c0392b;
    }

    /* Modal Footer */
    .settings-modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding: 16px 24px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .btn-cancel {
        padding: 10px 20px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .btn-cancel:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
    }

    .btn-save {
        padding: 10px 24px;
        background: linear-gradient(135deg, #00bcd4, #0097a7);
        border: none;
        border-radius: 8px;
        color: #fff;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(0, 188, 212, 0.3);
    }

    .btn-save:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 188, 212, 0.4);
    }

    /* Responsive */
    @media (max-width: 768px) {
        .settings-modal {
            width: 95%;
            max-height: 90vh;
        }

        .settings-modal-body {
            flex-direction: column;
        }

        .settings-sidebar {
            width: 100%;
            flex-direction: row;
            overflow-x: auto;
            padding: 12px;
        }

        .settings-nav-item {
            flex-shrink: 0;
            padding: 10px 14px;
        }

        .settings-nav-item span {
            display: none;
        }
    }

    window.activeGroupId = {{ group.id if group else 0 }};
    window.activeInput = null;
    window.activePickerPostId = null;

    const popularEmojis = ['????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '??????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '??????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????', '????'];

    function initPickers() {
        const emojiGrid = document.getElementById('emojiGrid');
        if (emojiGrid) {
            emojiGrid.innerHTML = '';
                const span = document.createElement('span');
                span.className = 'emoji-item';
                span.textContent = emoji;
                emojiGrid.appendChild(span);
            });
        }
        const stickerGrid = document.getElementById('stickerGrid');
        if (stickerGrid) {
            stickerGrid.innerHTML = '';
                const img = document.createElement('img');
                img.className = 'sticker-item';
                img.src = `https://api.dicebear.com/7.x/bottts/svg?seed=${i}`;
                img.title = `Sticker ${i}`;
                stickerGrid.appendChild(img);
            }
        }
    }

    // Initialize Lucide icons
    document.addEventListener('DOMContentLoaded', function () {
        try {
            if (window.lucide) if (window.lucide) lucide.createIcons();

        } catch (e) { console.warn('Lucide icons failed to load', e); }

        try {
            initPickers();
        } catch (e) { console.warn('Picker init failed', e); }

        const postInput = document.getElementById('postInput');
        if (postInput) {
                window.activeInput = postInput;
                window.activePickerPostId = null;
                console.log('Post input focused');
            };
        }

        // Tab toggle
            tab.addEventListener('click', function () {
                this.classList.add('active');
            });
        });

        // Vote button toggle
            btn.addEventListener('click', function () {
                const isUpvote = this.classList.contains('upvote');
                const parent = this.closest('.vote-column');
                const oppositeBtn = parent.querySelector(isUpvote ? '.downvote' : '.upvote');

                this.classList.toggle('active');
                if (this.classList.contains('active')) {
                    oppositeBtn.classList.remove('active');
                }
            });
        });

        // Join button - calls API to actually join/leave
        const joinBtn = document.getElementById('joinBtn');
        if (joinBtn) {
            joinBtn.addEventListener('click', async function () {
                const isJoined = this.classList.contains('joined');
                const groupId = this.dataset.groupId;
                const endpoint = isJoined ? `/group/${groupId}/leave` : `/group/${groupId}/join`;

                try {
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    const data = await response.json();

                    if (data.success) {
                        if (isJoined) {
                            // Left group
                            this.classList.remove('joined');
                            this.querySelector('span').textContent = 'Join Group';
                            this.querySelector('i, svg').setAttribute('data-lucide', 'user-plus');
                        } else {
                            // Joined group
                            this.classList.add('joined');
                            this.querySelector('span').textContent = 'Joined';
                            this.querySelector('i, svg').setAttribute('data-lucide', 'check');

                            // Immediate achievement notification
                            if (data.new_achievements && data.new_achievements.length > 0) {
                                data.new_achievements.forEach(ach => {
                                    if (window.showAchievementNotification) {
                                        window.showAchievementNotification(ach);
                                    }
                                });
                            }
                        }

                        // Re-render icons
                        if (window.lucide) lucide.createIcons();

                    } else {
                        alert(data.message || 'Action failed');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Could not connect to server');
                }
            });
        }

        // ===== SETTINGS MODAL FUNCTIONALITY =====
        const settingsModal = document.getElementById('settingsModal');
        const settingsBtn = document.querySelector('.btn-settings');
        const closeSettingsBtn = document.getElementById('closeSettingsBtn');
        const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
        const settingsNavItems = document.querySelectorAll('.settings-nav-item');

        // Open settings modal
        if (settingsBtn) {
            settingsBtn.addEventListener('click', function () {
                settingsModal.classList.add('active');
                document.body.style.overflow = 'hidden';
            });
        }

        // Close settings modal
        function closeModal() {
            settingsModal.classList.remove('active');
            document.body.style.overflow = '';
        }

        if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', closeModal);
        if (cancelSettingsBtn) cancelSettingsBtn.addEventListener('click', closeModal);

        settingsModal.addEventListener('click', function (e) {
            if (e.target === settingsModal) closeModal();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && settingsModal.classList.contains('active')) closeModal();
        });

            item.addEventListener('click', function () {
                const tabId = this.dataset.tab;
                this.classList.add('active');
                document.getElementById('tab-' + tabId).classList.add('active');
                if (window.lucide) lucide.createIcons();

            });
        });

        const colorPicker = document.querySelector('.settings-color-picker');
        const colorHex = document.querySelector('.color-hex');
        if (colorPicker && colorHex) {
            colorPicker.addEventListener('input', function () {
                colorHex.textContent = this.value;
            });
        }

        const saveSettingsBtn = document.getElementById('saveSettingsBtn');
        if (saveSettingsBtn) {
            let uploadedIconUrl = "{{ group.icon_url }}";
            let uploadedBannerUrl = "{{ group.banner_url }}";

            const uploadIconBtn = document.getElementById('uploadIconBtn');
            const groupIconInput = document.getElementById('groupIconInput');
            const iconPreviewImg = document.querySelector('.icon-preview img') || document.querySelector('.icon-preview');

            if (groupIconInput) {
                groupIconInput.addEventListener('change', async function () {
                    if (this.files && this.files[0]) {
                        const formData = new FormData();
                        formData.append('file', this.files[0]);
                        try {
                            const response = await fetch(`/group/{{ group.id }}/upload-icon`, { method: 'POST', body: formData });
                            const result = await response.json();
                            if (result.success) {
                                uploadedIconUrl = result.url;
                                if (iconPreviewImg.tagName === 'IMG') iconPreviewImg.src = result.url;
                            } else alert(result.message);
                        } catch (err) { console.error(err); alert('Upload failed'); }
                    }
                });
            }

            const uploadBannerBtn = document.getElementById('uploadBannerBtn');
            const groupBannerInput = document.getElementById('groupBannerInput');
            const bannerPreviewImg = document.querySelector('.banner-preview img') || document.querySelector('.banner-preview');

            if (groupBannerInput) {
                groupBannerInput.addEventListener('change', async function () {
                    if (this.files && this.files[0]) {
                        const formData = new FormData();
                        formData.append('file', this.files[0]);
                        try {
                            const response = await fetch(`/group/{{ group.id }}/upload-banner`, { method: 'POST', body: formData });
                            const result = await response.json();
                            if (result.success) {
                                uploadedBannerUrl = result.url;
                                if (bannerPreviewImg.tagName === 'IMG') bannerPreviewImg.src = result.url;
                            } else alert(result.message);
                        } catch (err) { console.error(err); alert('Upload failed'); }
                    }
                });
            }

            saveSettingsBtn.addEventListener('click', async function () {
                const data = {
                    name: document.getElementById('settingsGroupName').value,
                    description: document.getElementById('settingsGroupDesc').value,
                    group_type: document.getElementById('settingsGroupCategory').value,
                    category: document.getElementById('settingsGroupCategory').value,
                    icon_url: uploadedIconUrl,
                    banner_url: uploadedBannerUrl
                };
                try {
                    const response = await fetch(`/group/{{ group.id }}/update`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    if (result.success) {
                        alert('Settings saved!');
                        location.reload();
                    } else alert(result.message);
                } catch (error) { console.error(error); alert('Failed to save'); }
            });
        }

        // ===== ADVANCED POSTING FEATURES =====
        let selectedMangaLinks = [];
        let postAttachments = [];

        const attachImageBtn = document.getElementById('attachImageBtn');
        const attachFileBtn = document.getElementById('attachFileBtn');
        const linkMangaBtn = document.getElementById('linkMangaBtn');
        const imageInput = document.getElementById('imageInput');
        const fileInput = document.getElementById('fileInput');
        const attachmentPreviews = document.getElementById('attachmentPreviews');
        const mangaSearchResults = document.getElementById('mangaSearchResults');
        const postInput = document.getElementById('postInput');
        const submitPostBtn = document.getElementById('submitPostBtn');


        function handleFileSelection(files, type) {
            for (let file of files) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const id = Date.now() + Math.random();
                    postAttachments.push({ id, file, type });
                    const div = document.createElement('div');
                    div.className = 'attachment-preview';
                    div.id = `attach-${id}`;
                    attachmentPreviews.appendChild(div);
                    if (window.lucide) lucide.createIcons();

                }
                reader.readAsDataURL(file);
            }
        }


        window.removeAttachment = function (id) {
            document.getElementById(`attach-${id}`).remove();
        };

        // Manga search popup elements
        const mangaSearchPopup = document.getElementById('mangaSearchPopup');
        const mangaSearchInput = document.getElementById('mangaSearchInput');

        if (linkMangaBtn) {
                mangaSearchPopup.classList.toggle('active');
                if (mangaSearchPopup.classList.contains('active')) {
                    searchManga(''); // Load all manga initially
                        mangaSearchInput.focus();
                        if (window.lucide) lucide.createIcons();

                    }, 100);
                }
            });
        }

        window.closeMangaPopup = function () {
            mangaSearchPopup.classList.remove('active');
            mangaSearchInput.value = '';
        };

        // Search input handler
        if (mangaSearchInput) {
            let searchTimeout;
            mangaSearchInput.addEventListener('input', function () {
                clearTimeout(searchTimeout);
                    searchManga(this.value.trim());
                }, 300);
            });
        }

        // #@ shortcut for manga linking - detect #@manga-name pattern
        if (postInput) {
            postInput.addEventListener('input', function (e) {
                const value = this.value;
                const match = value.match(/#@([a-zA-Z0-9-]+)$/);

                if (match) {
                    const searchTerm = match[1]; // e.g., "solo-leveling" or "one-piece"
                    mangaSearchPopup.classList.add('active');
                    mangaSearchInput.value = searchTerm.replace(/-/g, ' ');
                    searchManga(searchTerm);
                    if (window.lucide) lucide.createIcons();

                }
            });

            // Handle keyboard navigation in search
            postInput.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    mangaSearchPopup.classList.remove('active');
                }
            });
        }

        async function searchManga(query) {
            try {
                if (window.lucide) lucide.createIcons();


                const response = await fetch(`/api/manga/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                renderMangaResults(data, query);
            } catch (err) { console.error(err); }
        }

        function renderMangaResults(results) {
            mangaSearchResults.innerHTML = '';
            if (results.length === 0) {
                return;
            }
                const item = document.createElement('div');
                item.className = 'manga-search-item';
                const coverUrl = m.cover || 'https://via.placeholder.com/40x56?text=No+Cover';
                mangaSearchResults.appendChild(item);
            });
        }

        function selectManga(manga) {
                selectedMangaLinks.push(manga);
                const div = document.createElement('div');
                div.className = 'attachment-preview';
                div.id = `manga-${manga.id}`;
                attachmentPreviews.appendChild(div);
            }

            // Remove #@... pattern from input if used
            if (postInput && postInput.value.includes('#@')) {
                postInput.value = postInput.value.replace(/#@[a-zA-Z0-9-]*$/, '').trim();
            }

            // Close popup and clear search
            mangaSearchPopup.classList.remove('active');
            mangaSearchInput.value = '';
        }

        window.removeMangaLink = function (id) {
            document.getElementById(`manga-${id}`).remove();
        };

        if (submitPostBtn) {
            submitPostBtn.addEventListener('click', async function () {
                const content = postInput.value.trim();

                // Collect external attachments (GIFs, Stickers)
                const externalAttachments = [];
                    if (div.dataset.url) {
                        externalAttachments.push({
                            url: div.dataset.url,
                            type: div.dataset.type
                        });
                    }
                });

                if (!content && postAttachments.length === 0 && externalAttachments.length === 0 && selectedMangaLinks.length === 0) return;

                const formData = new FormData();
                formData.append('content', content);
                formData.append('external_attachments', JSON.stringify(externalAttachments));

                try {
                    submitPostBtn.disabled = true;
                    if (window.lucide) lucide.createIcons();

                    const response = await fetch(`/group/{{ group.id }}/post`, { method: 'POST', body: formData });
                    const result = await response.json();
                    if (result.success) location.reload();
                    else {
                    }
                } catch (err) {
                }
            });
        }

        // ===== COMMENTS LOGIC =====
        window.toggleComments = async function (postId) {
            const section = document.getElementById(`comments-section-${postId}`);
            if (!section) return;
            section.style.display = section.style.display === 'block' ? 'none' : 'block';
            if (section.style.display === 'block') window.loadComments(postId);
        };

        window.loadComments = async function (postId) {
            const list = document.getElementById(`comment-list-${postId}`);
            if (window.lucide) lucide.createIcons();

            try {
                const response = await fetch(`/group/post/${postId}/comments`);
                const comments = await response.json();
                list.innerHTML = '';
                if (comments.length === 0) {
                    return;
                }
                    const item = document.createElement('div');
                    item.className = 'comment-item';

                    let attachmentsHtml = '';
                            if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'sticker'].includes(a.type)) {
                            } else {
                            }
                        });
                    }

                    item.innerHTML = `
                            ${attachmentsHtml}
                    list.appendChild(item);
                });
                if (window.lucide) lucide.createIcons();

            } catch (err) {
                console.error(err);
            }
        }

        window.likeComment = async function (commentId, btn) {
            try {
                const response = await fetch(`/group/comment/${commentId}/like`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    const countSpan = btn.querySelector('.like-count');
                    countSpan.textContent = result.like_count;
                    if (result.status === 'liked') btn.classList.add('active');
                    else btn.classList.remove('active');
                }
            } catch (err) { console.error(err); }
        };

        // Comment Attachments State
        window.commentAttachmentsStore = {};

        window.triggerCommentFile = function (postId, type) {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = type === 'image' ? 'image/*' : '.pdf,.doc,.docx,.txt';
            input.multiple = true;
            input.click();
        };

        window.handleCommentFileSelection = function (postId, files, type) {
            if (!window.commentAttachmentsStore[postId]) window.commentAttachmentsStore[postId] = [];

            for (let file of files) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const id = Date.now() + Math.random();
                    window.commentAttachmentsStore[postId].push({ id, file, type });
                    window.renderCommentPreviews(postId);
                };
                reader.readAsDataURL(file);
            }
        }

        window.renderCommentPreviews = function (postId) {
            const container = document.getElementById(`comment-previews-${postId}`);
            if (!container) return;
            container.innerHTML = '';
                const div = document.createElement('div');
                div.className = 'attachment-preview mini';
                if (a.type === 'image') {
                    const reader = new FileReader();
                    reader.readAsDataURL(a.file);
                } else {
                }
                container.appendChild(div);
            });
            if (window.lucide) lucide.createIcons();

        }

        window.removeCommentAttach = function (postId, attachId) {
            window.renderCommentPreviews(postId);
        };

        window.submitComment = async function (postId, event) {
            const input = document.getElementById(`comment-input-${postId}`);
            const content = input.value.trim();
            const attachments = window.commentAttachmentsStore[postId] || [];

            // Collect external attachments (GIFs, Stickers)
            const externalAttachments = [];
            const previewContainer = document.getElementById(`comment-previews-${postId}`);
            if (previewContainer) {
                    if (div.dataset.url) {
                        externalAttachments.push({
                            url: div.dataset.url,
                            type: div.dataset.type
                        });
                    }
                });
            }

            if (!content && attachments.length === 0 && externalAttachments.length === 0) return;

            const submitBtn = event ? event.currentTarget : null;
            if (!submitBtn) {
                console.error('Submit button not found in event');
                return;
            }
            const originalHtml = submitBtn.innerHTML;

            try {
                submitBtn.disabled = true;
                if (window.lucide) lucide.createIcons();


                const formData = new FormData();
                formData.append('content', content);
                formData.append('external_attachments', JSON.stringify(externalAttachments));

                const response = await fetch(`/group/post/${postId}/comment`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    input.value = '';
                    window.commentAttachmentsStore[postId] = [];
                    window.renderCommentPreviews(postId);
                    window.loadComments(postId);
                    const countSpan = document.getElementById(`comment-count-${postId}`);
                    const currentCount = parseInt(countSpan.textContent) || 0;
                    countSpan.textContent = `${currentCount + 1} Comments`;
                } else alert(result.message);
            } catch (err) {
                console.error(err);
                alert('Failed to post comment');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
                if (window.lucide) lucide.createIcons();

            }
        };

        // Edit Post Functions
        window.editPost = function (postId, content) {
            const modal = document.getElementById('editPostModal');
            const postIdInput = document.getElementById('editPostId');
            const contentInput = document.getElementById('editPostContent');

            postIdInput.value = postId;
            contentInput.value = content;
            modal.classList.add('active');
            contentInput.focus();
            if (window.lucide) lucide.createIcons();

        };

        window.closeEditModal = function () {
            const modal = document.getElementById('editPostModal');
            modal.classList.remove('active');
        };

        window.saveEditedPost = async function () {
            const postId = document.getElementById('editPostId').value;
            const content = document.getElementById('editPostContent').value.trim();

            if (!content) {
                alert('Content cannot be empty');
                return;
            }

            try {
                const response = await fetch(`/group/post/${postId}/edit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                const result = await response.json();

                if (result.success) {
                    closeEditModal();
                    location.reload(); // Reload to show updated content
                } else {
                    alert(result.message || 'Failed to update post');
                }
            } catch (err) {
                console.error(err);
                alert('Failed to update post');
            }
        };

        window.deletePost = async function (postId) {
            if (!confirm('Are you sure you want to delete this post? This cannot be undone.')) {
                return;
            }

            try {
                const response = await fetch(`/group/post/${postId}/delete`, {
                    method: 'POST'
                });
                const result = await response.json();

                if (result.success) {
                    // Remove the post element from DOM
                    const postCard = document.querySelector(`.post-card[data-post-id="${postId}"]`);
                    if (postCard) {
                        postCard.remove();
                    } else {
                        location.reload(); // Fallback to reload
                    }
                } else {
                    alert(result.message || 'Failed to delete post');
                }
            } catch (err) {
                console.error(err);
                alert('Failed to delete post');
            }
        };

        // Close edit modal on Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                closeEditModal();
            }
        });

        // Voting Function
        window.votePost = async function (postId, vote, btn) {
            try {
                const response = await fetch(`/group/post/${postId}/vote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ vote })
                });
                const result = await response.json();

                if (result.success) {
                    // Find post card and update UI
                    const postCard = document.querySelector(`.post-card[data-post-id="${postId}"]`);
                    const voteCol = postCard.querySelector('.vote-column');
                    const upBtn = voteCol.querySelector('.upvote');
                    const downBtn = voteCol.querySelector('.downvote');
                    const upCount = upBtn.querySelector('.upvote-count');
                    const downCount = downBtn.querySelector('.downvote-count');

                    // Update counts
                    upCount.textContent = result.upvotes;
                    downCount.textContent = result.downvotes;

                    // Update button states
                    upBtn.classList.remove('active');
                    downBtn.classList.remove('active');

                    if (result.new_vote === 1) {
                        upBtn.classList.add('active');
                    } else if (result.new_vote === -1) {
                        downBtn.classList.add('active');
                    }
                }
            } catch (err) {
                console.error('Vote error:', err);
            }
        };

        // Channel Functions
        window.showAddChannelModal = function () {
            const name = prompt('Enter channel name:');
            if (name && name.trim()) {
                window.createChannel(name.trim());
            }
        };

        window.createChannel = async function (name) {
            try {
                const response = await fetch(`/group/{{ group.id }}/channels`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, type: 'text' })
                });
                const result = await response.json();

                if (result.success) {
                    // Add new channel to list
                    const list = document.getElementById('channelsList');
                    const div = document.createElement('div');
                    div.className = 'channel-item';
                    div.dataset.channelId = result.channel_id;
                    list.appendChild(div);
                    if (window.lucide) lucide.createIcons();

                } else {
                    alert(result.message || 'Failed to create channel');
                }
            } catch (err) {
                console.error(err);
                alert('Failed to create channel');
            }
        }

        // Mention System
        const mentionDropdown = document.getElementById('mentionDropdown');
        const mentionList = document.getElementById('mentionList');
        const mentionBtn = document.getElementById('mentionBtn');
        let mentionQuery = '';
        let mentionStartPos = -1;

        // Open mention dropdown from button
        if (mentionBtn) {
                if (postInput) {
                    // Insert @ at cursor position
                    const pos = postInput.selectionStart;
                    const text = postInput.value;
                    postInput.value = text.slice(0, pos) + '@' + text.slice(pos);
                    postInput.focus();
                    postInput.selectionStart = postInput.selectionEnd = pos + 1;
                    mentionStartPos = pos;
                    mentionQuery = '';
                    searchMentions('');
                    mentionDropdown.classList.add('active');
                }
            });
        }

        // Detect @ while typing in any textarea
        document.addEventListener('input', function (e) {
            if (e.target.classList.contains('comment-input') || e.target.id === 'post_content_input' || e.target.id === 'postInput' || e.target.tagName === 'TEXTAREA') {
                const text = e.target.value;
                const pos = e.target.selectionStart;

                // Check if we're in a mention
                const beforeCursor = text.slice(0, pos);
                const mentionMatch = beforeCursor.match(/@([a-zA-Z0-9_-]*)$/);

                if (mentionMatch) {
                    mentionStartPos = pos - mentionMatch[0].length;
                    mentionQuery = mentionMatch[1];
                    window.activeInput = e.target;
                    searchMentions(mentionQuery);

                    // Position dropdown near the input
                    const rect = e.target.getBoundingClientRect();
                    mentionDropdown.style.left = `${rect.left}px`;
                    mentionDropdown.style.width = `${rect.width}px`;
                    mentionDropdown.style.bottom = `${window.innerHeight - rect.top + 5}px`;
                    mentionDropdown.style.position = 'fixed'; // Use fixed for better positioning across multiple inputs

                    mentionDropdown.classList.add('active');
                } else {
                    mentionDropdown.classList.remove('active');
                    mentionStartPos = -1;
                }
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && mentionDropdown.classList.contains('active')) {
                mentionDropdown.classList.remove('active');
                e.preventDefault();
            }
        });


        async function searchMentions(query) {
            try {
                const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}&group_id={{ group.id }}`);
                const results = await response.json();
                renderMentionResults(results);
            } catch (err) {
                console.error('Mention search error:', err);
            }
        }

        function renderMentionResults(results) {
            mentionList.innerHTML = '';

            if (results.length === 0) {
                return;
            }

                const item = document.createElement('div');
                item.className = 'mention-item';

                let avatarHtml = '';
                let usernameClass = '';
                let badgeHtml = '';
                let descHtml = '';

                if (m.type === 'special') {
                    usernameClass = 'special';
                } else if (m.type === 'role') {
                    usernameClass = 'role';
                } else {
                }

                item.innerHTML = `
                    ${avatarHtml}
                        ${descHtml}
                    ${badgeHtml}
                `;

                mentionList.appendChild(item);
            });

            if (window.lucide) lucide.createIcons();

        }

        function selectMention(mention) {
                const text = activeInput.value;
                const before = text.slice(0, mentionStartPos);
                const after = text.slice(mentionStartPos).replace(/^@[a-zA-Z0-9_-]*/, '');

                // Use specified username (might be mod-username)
                const mentionUser = mention.username;
                activeInput.value = before + '@' + mentionUser + ' ' + after.trimStart();
                activeInput.focus();

                // Set cursor after the mention
                const newPos = mentionStartPos + mentionUser.length + 2;
                activeInput.selectionStart = activeInput.selectionEnd = newPos;
            }

            mentionDropdown.classList.remove('active');
            mentionStartPos = -1;
        }

        // Interactive Pickers (Emoji, GIF, Stickers, Gifts)

        window.togglePicker = function (pickerId, postId = null, btn = null) {
            const picker = document.getElementById(pickerId);
            const isActive = picker.classList.contains('active');
            const targetBtn = btn || (window.event ? window.event.currentTarget : null);

            // Close all pickers first
            closePickers();

            if (!isActive) {
                activePickerPostId = postId;
                picker.classList.add('active');

                // If postId is present, reposition picker near the button
                if (postId && targetBtn) {
                    const rect = targetBtn.getBoundingClientRect();
                    picker.style.position = 'fixed';
                    picker.style.left = `${rect.left}px`;
                    // Adjust bottom based on space
                    picker.style.bottom = `${window.innerHeight - rect.top + 5}px`;
                    picker.style.width = '280px';
                } else {
                    // Reset to relative positioning for main post input
                    picker.style.position = 'absolute';
                    picker.style.left = '0';
                    picker.style.bottom = '100%';
                    picker.style.width = '300px';
                }
            }
        };

        window.closePickers = function () {
            activePickerPostId = null;
        };

        // Close pickers on click outside
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.picker-popover') && !e.target.closest('.post-action-icon') && !e.target.closest('.comment-extra-btn')) {
                closePickers();
            }
        });

        window.insertEmoji = function (emoji) {
            let input = window.activeInput;
            if (!input) {
                if (window.activePickerPostId) {
                    input = document.getElementById(`comment-input-${window.activePickerPostId}`);
                } else {
                    input = document.getElementById('postInput');
                }
            }

            if (input) {
                const start = input.selectionStart;
                const end = input.selectionEnd;
                const text = input.value;
                input.value = text.slice(0, start) + emoji + text.slice(end);
                input.selectionStart = input.selectionEnd = start + emoji.length;
                input.focus();
            }
            closePickers();
        }

        window.searchGIFs = async function (query) {
            const grid = document.getElementById('gifGrid');
            if (!grid) return;


            try {
                // Using a public proxy or placeholder for now if no API key
                // For demonstration, we'll fetch from Tenor if we have a key, but here we mockup
                const results = [
                    'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzcmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/3o7TKDkDbIDJieKbVm/giphy.gif',
                    'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzcmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/l0HlO4f8pI9o0hY8w/giphy.gif',
                    'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzcmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/3o7TKuylLbfwAFv7Tq/giphy.gif',
                    'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzc0NmIzZjRmMzcmZXA9djFfaW50ZXJuYWxfZ2lmX2J5X2lkJmN0PWc/l0HlHFRbZyYPC08D6/giphy.gif'
                ];

                grid.innerHTML = '';
                    const img = document.createElement('img');
                    img.className = 'gif-item';
                    img.src = url;
                    grid.appendChild(img);
                });
            } catch (err) {
            }
        }

        window.insertGIF = function (url) {
            // GIFs and Stickers added to attachments
            console.log('Inserting GIF:', url);
            window.addExternalAttachment(url, 'gif');
            window.closePickers();
        }

        window.insertSticker = function (url) {
            console.log('Inserting Sticker:', url);
            window.addExternalAttachment(url, 'sticker');
            window.closePickers();
        }

        window.addExternalAttachment = function (url, type) {
            let previewsContainerId = 'attachmentPreviews';
            if (window.activePickerPostId) {
                previewsContainerId = `comment-previews-${window.activePickerPostId}`;
            }

            const previews = document.getElementById(previewsContainerId);
            if (previews) {
                const div = document.createElement('div');
                div.className = 'attachment-preview';
                div.dataset.url = url;
                div.dataset.type = type;
                div.innerHTML = `
                `;
                previews.appendChild(div);
            }
        }

        // Poll Modal - Initialize after a short delay to ensure modal exists
        setTimeout(function () {
            const pollModal = document.getElementById('pollModal');
            const pollBtn = document.getElementById('pollBtn');
            const closePollBtn = document.getElementById('closePollBtn');
            const pollOptionsList = document.getElementById('pollOptionsList');
            const createRealPollBtn = document.getElementById('createRealPollBtn');

            if (pollBtn) {
                    const modal = document.getElementById('pollModal');
                    if (modal) modal.classList.add('active');
                };
            }

            window.closePollModal = function () {
                const modal = document.getElementById('pollModal');
                if (modal) modal.classList.remove('active');
            };

            if (closePollBtn) {
                closePollBtn.onclick = window.closePollModal;
            }

            window.addPollOption = function () {
                const list = document.getElementById('pollOptionsList');
                if (!list) return;
                const count = list.querySelectorAll('.poll-option').length + 1;
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'settings-input poll-option';
                input.placeholder = `Option ${count}`;
                list.appendChild(input);
            };

            if (createRealPollBtn) {
                createRealPollBtn.onclick = async function () {
                    const question = document.getElementById('pollQuestion').value.trim();
                    const optionInputs = document.querySelectorAll('.poll-option');

                        alert('Question and at least 2 options are required');
                        return;
                    }

                    try {
                        createRealPollBtn.disabled = true;
                        createRealPollBtn.textContent = 'Creating...';

                        const response = await fetch(`/group/${window.activeGroupId}/poll`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                question,
                                options,
                                allow_multiple: false,
                                expires_in: 7
                            })
                        });

                        const result = await response.json();
                        if (result.success) {
                            location.reload();
                        } else {
                            alert(result.message);
                        }
                    } catch (err) {
                        console.error(err);
                        alert('Failed to create poll');
                    } finally {
                        createRealPollBtn.disabled = false;
                        createRealPollBtn.textContent = 'Create Poll';
                    }
                };
            }
        }, 100);

        window.togglePollOption = function (pollId, optionId, allowMultiple) {
            const pollDiv = document.getElementById(`poll-${pollId}`);
            if (pollDiv.querySelector('.poll-option-btn.voted')) return;

            const btn = pollDiv.querySelector(`.poll-option-btn[data-option-id="${optionId}"]`);

            if (!allowMultiple) {
            }

            btn.classList.toggle('selected');

            const selectedCount = pollDiv.querySelectorAll('.poll-option-btn.selected').length;
            const voteBtn = document.getElementById(`vote-btn-${pollId}`);
            if (voteBtn) voteBtn.disabled = (selectedCount === 0);
        };

        window.submitPollVote = async function (pollId) {
            const pollDiv = document.getElementById(`poll-${pollId}`);

            if (selectedOptions.length === 0) return;

            const btn = document.getElementById(`vote-btn-${pollId}`);
            try {
                btn.disabled = true;
                btn.textContent = 'Voting...';

                const response = await fetch(`/group/poll/${pollId}/vote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ option_ids: selectedOptions })
                });

                const result = await response.json();
                if (result.success) {
                    location.reload(); // Simple refresh to show new percentages
                } else {
                    alert(result.message);
                }
            } catch (err) {
                console.error(err);
                alert('Failed to submit vote');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Vote';
            }
        };
    });

                style="width: 100%; justify-content: center; margin-top: 10px; background: rgba(0, 188, 212, 0.1); color: #00bcd4;"

{% endblock %}
