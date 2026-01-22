from django.contrib import admin
from .models import Course, Lesson, Membership, Payment

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_vip', 'created_at')
    list_filter = ('category', 'is_vip')
    search_fields = ('title', 'description')
    inlines = [LessonInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'thumbnail', 'category')
        }),
        ('Settings', {
            'fields': ('is_vip',),
            'classes': ('collapse',)
        }),
    )

from django_summernote.admin import SummernoteModelAdmin

@admin.register(Lesson)
class LessonAdmin(SummernoteModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'content')
    ordering = ('course', 'order')
    summernote_fields = ('content',)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_vip', 'expiry_date', 'is_active')
    list_filter = ('is_vip',)
    search_fields = ('user__email', 'user__name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'reference', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'reference')
    readonly_fields = ('created_at', 'updated_at')
