from datetime import datetime


def year(request):
    """Добавляет переменную year с текущим годом."""
    return {
        "year": datetime.today().year,
    }
