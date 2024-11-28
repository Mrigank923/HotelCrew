from django.urls import path
from .views import Taskassignment,TaskDeleteView,TaskUpdateView,AllTaskListView,StaffTaskListView,TaskStatusUpdateView,AnnouncementListCreateView,AnnouncementDetailView,AllTaskDayListView,AllAnnouncementDayListView,AvailableStaffListView

urlpatterns = [
    path('tasks/', Taskassignment.as_view(), name='task-create'),
    path('tasks/delete/<int:pk>/', TaskDeleteView.as_view()),
    path('tasks/update/<int:pk>/', TaskUpdateView.as_view()),
    path('tasks/all/', AllTaskListView.as_view()),
    path('tasks/staff/',StaffTaskListView.as_view()),
    path('tasks/status/<int:pk>/', TaskStatusUpdateView.as_view(),),
    path('announcements/', AnnouncementListCreateView.as_view(), name='announcement-list-create'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('tasks/day/', AllTaskDayListView.as_view()),
    path('announcements/day/', AllAnnouncementDayListView.as_view()),
    path('staff/available/', AvailableStaffListView.as_view()),
    
   
]