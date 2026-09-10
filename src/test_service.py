from ktu_service import KtuService

service = KtuService(user_id="demo_user")


# Exam mode
a = exam = service.get_exam_mode("Operating Systems")
print(a)