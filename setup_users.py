from core.models import User

# Create teacher account
teacher, created = User.objects.get_or_create(
    username='teacher1',
    defaults={
        'email': 'teacher1@reviewverse.com',
        'is_teacher': True,
        'is_staff': True
    }
)
if created:
    teacher.set_password('Teacher@123')
    teacher.save()
    print("✓ Teacher created: teacher1 / Teacher@123")
else:
    teacher.set_password('Teacher@123')
    teacher.save()
    print("✓ Teacher updated: teacher1 / Teacher@123")

# Create student account  
student, created = User.objects.get_or_create(
    username='student1',
    defaults={
        'email': 'student1@reviewverse.com',
        'is_student': True
    }
)
if created:
    student.set_password('Student@123')
    student.save()
    print("✓ Student created: student1 / Student@123")
else:
    student.set_password('Student@123')
    student.save()
    print("✓ Student updated: student1 / Student@123")

print("\n✅ All accounts ready!")
