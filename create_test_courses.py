import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvp_django.settings')
django.setup()

from learn_crypto.models import Course, Lesson

def create_test_data():
    print("Creating test courses...")
    
    # Create Crypto Course
    crypto_course, created = Course.objects.get_or_create(
        title="Bitcoin Basics",
        defaults={
            'description': "Learn the fundamentals of Bitcoin, blockchain, and how to start trading.",
            'category': 'crypto',
            'is_vip': False
        }
    )
    if created:
        print(f"Created course: {crypto_course.title}")
        Lesson.objects.create(
            course=crypto_course,
            title="What is Bitcoin?",
            content="Bitcoin is a decentralized digital currency...",
            video_url="https://www.youtube.com/embed/Gc2en3nHxA4",
            order=1
        )
        Lesson.objects.create(
            course=crypto_course,
            title="How to Buy Bitcoin",
            content="You can buy Bitcoin on exchanges like WestLinks...",
            video_url="https://www.youtube.com/embed/41JCpzvnn_0",
            order=2
        )
    else:
        print(f"Course already exists: {crypto_course.title}")

    # Create Forex Course (VIP)
    forex_course, created = Course.objects.get_or_create(
        title="Advanced Forex Strategies",
        defaults={
            'description': "Master technical analysis and profitable trading strategies.",
            'category': 'forex',
            'is_vip': True
        }
    )
    if created:
        print(f"Created course: {forex_course.title}")
        Lesson.objects.create(
            course=forex_course,
            title="Understanding Pips and Lots",
            content="In Forex, price movements are measured in pips...",
            video_url="https://www.youtube.com/embed/p7HKvqRI_Bo",
            order=1
        )
    else:
        print(f"Course already exists: {forex_course.title}")

    print("Test data creation complete!")

if __name__ == "__main__":
    create_test_data()
