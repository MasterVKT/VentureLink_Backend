from rest_framework.pagination import PageNumberPagination


class ProjectPagination(PageNumberPagination):
    """
    Pagination pour la liste des projets.
    20 projets par page pour un chargement rapide sur mobile.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100  # Limite maximale