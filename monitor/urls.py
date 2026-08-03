from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('monitor/', views.monitor, name='monitor'),
    path('api/start_interview/', views.start_interview, name='start_interview'),
    path('api/end_interview/', views.end_interview, name='end_interview'),
    path('api/process_frame/', views.process_frame, name='process_frame'),
    path('api/log_tab_switch/', views.log_tab_switch, name='log_tab_switch'),
    path('api/send_audio_activity/', views.send_audio_activity, name='send_audio_activity'),
    path('api/get_candidate_details/', views.get_candidate_details, name='get_candidate_details'),
    
    # Interviewer Module
    path('interviewer/', views.interviewer_dashboard, name='interviewer_dashboard'),
    path('api/get_candidates/', views.get_candidate_list, name='get_candidate_list'),
    path('api/get_session_data/', views.get_candidate_session_data, name='get_candidate_session_data'),
    path('api/save_feedback/', views.save_feedback, name='save_feedback'),
    path('api/get_latest_frame/', views.get_latest_frame, name='get_latest_frame'),
]
