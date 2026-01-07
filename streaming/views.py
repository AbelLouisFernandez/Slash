import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StreamingService
from .services.tmdb import search_movie, get_movie_details, get_watch_providers


#Helper Function
def choose_platform_with_price(providers, country="IN"):
    """
    providers: list of provider dicts from TMDb (flatrate)
    """
    available_names = [p["provider_name"] for p in providers]

    services_in_db = StreamingService.objects.filter(
        name__in=available_names,
        country=country
    )

    if services_in_db.exists():
        cheapest = min(services_in_db, key=lambda s: s.monthly_price)
        return {
            "platform": cheapest.name,
            "price": float(cheapest.monthly_price),
            "source": "database"
        }

    # fallback: take first available platform
    return {
        "platform": available_names[0] if available_names else "Unavailable",
        "price": None,
        "source": "fallback"
    }
    


@csrf_exempt
def calculate_rotation(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=400)

    data = json.loads(request.body)
    movie_titles = data.get("movies", [])
    hours_per_week = data.get("hours_per_week", 10)

    platform_groups = {}

    for title in movie_titles:
        search = search_movie(title)
        if not search["results"]:
            continue

        movie = search["results"][0]
        details = get_movie_details(movie["id"])
        providers = get_watch_providers(movie["id"], region="IN")

        runtime_minutes = details.get("runtime") or 120
        runtime_hours = round(runtime_minutes / 60, 2)

        flatrate = providers.get("flatrate", [])
        if not flatrate:
            platform_info = {
                "platform": "Unavailable",
                "price": None,
                "source": "none"
            }
        else:
            platform_info = choose_platform_with_price(flatrate)

        platform = platform_info["platform"]

        platform_groups.setdefault(platform, {
            "total_hours": 0,
            "price": platform_info["price"],
            "movies": []
        })

        platform_groups[platform]["movies"].append({
            "title": movie["title"],
            "hours": runtime_hours
        })

        platform_groups[platform]["total_hours"] += runtime_hours

    return JsonResponse(platform_groups)



import math

def weeks_needed(total_hours, hours_per_week):
    return math.ceil(total_hours / hours_per_week)

def months_needed(weeks):
    return math.ceil(weeks / 4)


def optimize_rotation(platform_groups):
    """
    platform_groups: dict from calculate_rotation()
    """

    def sort_key(item):
        platform, info = item

        movie_count = len(info["movies"])
        price = info["price"] if info["price"] is not None else float("inf")
        total_hours = info["total_hours"]

        return (
            movie_count,     # fewer movies first
            price,           # cheaper first
            total_hours      # less watch time first
        )

    sorted_platforms = sorted(
        platform_groups.items(),
        key=sort_key
    )

    return sorted_platforms


def build_rotation_plan(platform_groups, hours_per_week):
    ordered = optimize_rotation(platform_groups)

    plan = []
    current_month = 1
    total_cost = 0

    for platform, info in ordered:
        weeks = weeks_needed(info["total_hours"], hours_per_week)
        months = months_needed(weeks)

        cost = (info["price"] or 0) * months

        plan.append({
            "platform": platform,
            "start_month": current_month,
            "months": months,
            "movies": info["movies"],
            "monthly_price": info["price"],
            "cost": cost
        })

        current_month += months
        total_cost += cost

    return {
        "timeline": plan,
        "total_cost": total_cost
    }
