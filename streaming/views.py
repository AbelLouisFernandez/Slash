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
    hours_per_week = float(data.get("hours_per_week", 10))

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

        # Choose cheapest available platform in DB
        chosen_platform = None
        chosen_price = None

        for p in flatrate:
            service = StreamingService.objects.filter(
                name=p["provider_name"],
                country="IN"
            ).first()

            if service:
                if chosen_price is None or service.monthly_price < chosen_price:
                    chosen_platform = service.name
                    chosen_price = float(service.monthly_price)

        # Fallback: first available platform
        if not chosen_platform:
            if flatrate:
                chosen_platform = flatrate[0]["provider_name"]
                chosen_price = None
            else:
                chosen_platform = "Unavailable"
                chosen_price = None

        platform_groups.setdefault(chosen_platform, {
            "movies": [],
            "total_hours": 0,
            "price": chosen_price
        })

        platform_groups[chosen_platform]["movies"].append({
            "title": movie["title"],
            "hours": runtime_hours
        })
        platform_groups[chosen_platform]["total_hours"] += runtime_hours

    # 🔥 BUILD TIMELINE HERE
    result = build_timeline(platform_groups, hours_per_week)

    return JsonResponse(result, safe=False)



import math

def weeks_needed(total_hours, hours_per_week):
    return math.ceil(total_hours / hours_per_week)

def months_needed(weeks):
    return max(1, math.ceil(weeks / 4))



def optimize_platform_order(platform_groups):
    """
    Sort by:
    1. Fewest movies
    2. Lowest price (None goes last)
    3. Lowest total hours
    """
    def sort_key(item):
        platform, info = item
        movie_count = len(info["movies"])
        price = info["price"] if info["price"] is not None else float("inf")
        total_hours = info["total_hours"]

        return (movie_count, price, total_hours)

    return sorted(platform_groups.items(), key=sort_key)

def build_timeline(platform_groups, hours_per_week):
    ordered = optimize_platform_order(platform_groups)

    timeline = []
    current_month = 1
    total_cost = 0

    for platform, info in ordered:
        weeks = weeks_needed(info["total_hours"], hours_per_week)
        months = months_needed(weeks)

        monthly_price = info["price"]
        cost = (monthly_price or 0) * months
        total_cost += cost

        for m in range(months):
            timeline.append({
                "month": current_month,
                "platform": platform,
                "monthly_price": monthly_price,
                "movies": info["movies"]
            })
            current_month += 1

    return {
        "timeline": timeline,
        "total_cost": total_cost
    }

