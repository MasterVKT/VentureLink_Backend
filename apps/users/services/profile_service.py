"""
Service for profile management.
"""
from django.db import transaction
from django.utils import timezone

from apps.users.models import (
    Profile, DomainExpertise, ProjectInterest,
    Education, Experience, Badge
)


class ProfileService:
    """Service for user profiles."""
    
    @staticmethod
    def update_profile(profile, data):
        """
        Update a user profile.
        
        Args:
            profile: Profile to update
            data: Dictionary with fields to update
            
        Returns:
            Updated Profile object
        """
        # Update fields
        for field, value in data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        # Save the profile
        profile.save()
        return profile
    
    @staticmethod
    def add_expertise(profile, domain, description=None, level=None):
        """
        Add a domain of expertise to a user profile.
        
        Args:
            profile: User profile
            domain: Domain of expertise
            description: Optional description
            level: Optional expertise level (1-5)
            
        Returns:
            Created DomainExpertise
        """
        return DomainExpertise.objects.create(
            profile=profile,
            domain=domain,
            description=description,
            level=level or 3
        )
    
    @staticmethod
    def remove_expertise(expertise_id):
        """
        Remove a domain of expertise.
        
        Args:
            expertise_id: The expertise ID to remove
        """
        DomainExpertise.objects.filter(id=expertise_id).delete()
    
    @staticmethod
    def add_interest(profile, category, specific_interest=None):
        """
        Add a project interest to a user profile.
        
        Args:
            profile: User profile
            category: Interest category
            specific_interest: Optional specific interest
            
        Returns:
            Created ProjectInterest
        """
        return ProjectInterest.objects.create(
            profile=profile,
            category=category,
            specific_interest=specific_interest
        )
    
    @staticmethod
    def remove_interest(interest_id):
        """
        Remove a project interest.
        
        Args:
            interest_id: The interest ID to remove
        """
        ProjectInterest.objects.filter(id=interest_id).delete()
    
    @staticmethod
    def add_education(profile, institution, degree, field_of_study, 
                    start_date, end_date=None, description=None, is_current=False):
        """
        Add education to a user profile.
        
        Args:
            profile: User profile
            institution: Educational institution
            degree: Degree obtained
            field_of_study: Field of study
            start_date: Start date
            end_date: Optional end date
            description: Optional description
            is_current: Whether this is current education
            
        Returns:
            Created Education
        """
        return Education.objects.create(
            profile=profile,
            institution=institution,
            degree=degree,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            description=description,
            is_current=is_current
        )
    
    @staticmethod
    def update_education(education_id, data):
        """
        Update education information.
        
        Args:
            education_id: The education ID to update
            data: Dictionary with fields to update
            
        Returns:
            Updated Education object
        """
        education = Education.objects.get(id=education_id)
        
        # If setting as current, clear end_date
        if data.get('is_current', False):
            data['end_date'] = None
        
        # Update fields
        for field, value in data.items():
            if hasattr(education, field):
                setattr(education, field, value)
        
        education.save()
        return education
    
    @staticmethod
    def remove_education(education_id):
        """
        Remove education.
        
        Args:
            education_id: The education ID to remove
        """
        Education.objects.filter(id=education_id).delete()
    
    @staticmethod
    def add_experience(profile, company, position, start_date, end_date=None, 
                     description=None, location=None, is_current=False):
        """
        Add professional experience to a user profile.
        
        Args:
            profile: User profile
            company: Company name
            position: Job position
            start_date: Start date
            end_date: Optional end date
            description: Optional job description
            location: Optional job location
            is_current: Whether this is a current job
            
        Returns:
            Created Experience
        """
        return Experience.objects.create(
            profile=profile,
            company=company,
            position=position,
            start_date=start_date,
            end_date=end_date,
            description=description,
            location=location,
            is_current=is_current
        )
    
    @staticmethod
    def update_experience(experience_id, data):
        """
        Update experience information.
        
        Args:
            experience_id: The experience ID to update
            data: Dictionary with fields to update
            
        Returns:
            Updated Experience object
        """
        experience = Experience.objects.get(id=experience_id)
        
        # If setting as current, clear end_date
        if data.get('is_current', False):
            data['end_date'] = None
        
        # Update fields
        for field, value in data.items():
            if hasattr(experience, field):
                setattr(experience, field, value)
        
        experience.save()
        return experience
    
    @staticmethod
    def remove_experience(experience_id):
        """
        Remove experience.
        
        Args:
            experience_id: The experience ID to remove
        """
        Experience.objects.filter(id=experience_id).delete()
    
    @staticmethod
    def award_badge(profile, badge_type, reason=None):
        """
        Award a badge to a user.
        
        Args:
            profile: User profile
            badge_type: Type of badge
            reason: Optional reason for awarding the badge
            
        Returns:
            Created Badge
        """
        return Badge.objects.create(
            profile=profile,
            badge_type=badge_type,
            reason=reason,
            awarded_at=timezone.now()
        ) 