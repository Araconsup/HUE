"""
Management command to seed realistic beauty and makeup products into HUE database.
"""

from django.core.management.base import BaseCommand
from core.models import ProductBrand, ProductCategory, Product, ProductShade


class Command(BaseCommand):
    help = "Seeds database with essential cosmetic categories, brands, products, and shades."

    def handle(self, *args, **options):
        self.stdout.write("Seeding HUE Beauty Database...")

        # 1. Categories
        categories_data = [
            ("Base & Foundation", "base", 1, "Liquid, cream, and powder foundation bases"),
            ("Concealer", "concealer", 2, "Under-eye and spot correcting concealers"),
            ("Bronzer & Contour", "bronzer", 3, "Warming bronzers and sculpting contours"),
            ("Blush", "blush", 4, "Liquid, cream, and powder cheek colors"),
            ("Highlighter", "highlighter", 5, "Luminizers and radiance enhancers"),
            ("Eyeshadow", "eyeshadow", 6, "Single pans, palettes, and cream shadows"),
            ("Eyeliner", "eyeliner", 7, "Pencil, gel, and liquid lash liners"),
            ("Mascara", "mascara", 8, "Volumizing, lengthening, and defining mascaras"),
            ("Brows", "brows", 9, "Gels, pencils, and sculpting waxes"),
            ("Lips", "lips", 10, "Lipsticks, lip oils, liners, and glosses"),
            ("Setting & Powder", "setting", 11, "Translucent powders and radiant setting mists"),
        ]

        cat_map = {}
        for name, slug, step_order, desc in categories_data:
            cat, _ = ProductCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "step_order": step_order, "description": desc}
            )
            cat_map[slug] = cat

        # 2. Brands
        brands_data = [
            ("Rare Beauty", "rare-beauty", "Mindfully crafted clean beauty by Selena Gomez", "https://www.rarebeauty.com"),
            ("Fenty Beauty", "fenty-beauty", "Beauty for all skintones by Rihanna", "https://fentybeauty.com"),
            ("NARS", "nars", "High-pigment runway makeup by François Nars", "https://www.narscosmetics.com"),
            ("MAC Cosmetics", "mac", "All Ages, All Races, All Genders professional artistry", "https://www.maccosmetics.com"),
            ("Charlotte Tilbury", "charlotte-tilbury", "Hollywood glamor and red-carpet glow", "https://www.charlottetilbury.com"),
            ("Maybelline New York", "maybelline", "Accessible high-performance urban cosmetics", "https://www.maybelline.com"),
            ("Glossier", "glossier", "Skin-first, makeup-second beauty essentials", "https://www.glossier.com"),
            ("Laura Mercier", "laura-mercier", "Flawless face pioneer & setting powders", "https://www.lauramercier.com"),
            ("e.l.f. Cosmetics", "elf", "Affordable viral beauty favorites", "https://www.elfcosmetics.com"),
            ("Dior Beauty", "dior", "Haute couture backstage beauty formulas", "https://www.dior.com")
        ]

        brand_map = {}
        for name, slug, desc, web in brands_data:
            b, _ = ProductBrand.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": desc, "website": web}
            )
            brand_map[slug] = b

        # 3. Products & Shades
        products_data = [
            # Base
            {
                "brand": "maybelline",
                "category": "base",
                "name": "Fit Me Matte + Poreless Foundation",
                "subcategory": "Liquid Foundation",
                "finish": "Natural Matte",
                "price": 8.99,
                "description": "Oil-free lightweight liquid foundation that refines pores and leaves a natural finish.",
                "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("110 Porcelain", "110", "#F2DFC8", "cool", "Fair with cool pink balance"),
                    ("120 Classic Ivory", "120", "#ECCBAE", "neutral", "Light with neutral balance"),
                    ("220 Natural Beige", "220", "#D8AA80", "warm", "Medium with warm yellow undertone"),
                    ("330 Toffee", "330", "#A8714C", "warm", "Deep-tan with warm undertone"),
                    ("360 Mocha", "360", "#6A432F", "neutral-warm", "Rich deep espresso warmth")
                ]
            },
            {
                "brand": "fenty-beauty",
                "category": "base",
                "name": "Pro Filt'r Soft Matte Longwear Foundation",
                "subcategory": "Liquid Foundation",
                "finish": "Soft Matte",
                "price": 40.00,
                "description": "Climate-adaptive soft matte foundation with buildable medium-to-full coverage.",
                "image_url": "https://images.unsplash.com/photo-1631730486784-5456119f69ae?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("150 Neutral", "150", "#E8C8AA", "neutral", "Light neutral with peach tone"),
                    ("240 Warm Neutral", "240", "#CD976D", "warm", "Medium with subtle gold warmth"),
                    ("370 Warm Bronze", "370", "#9E643E", "warm", "Deep bronze with caramel warmth"),
                    ("420 Deep Neutral", "420", "#663B25", "neutral-warm", "Deep rich neutral")
                ]
            },
            # Concealer
            {
                "brand": "nars",
                "category": "concealer",
                "name": "Radiant Creamy Concealer",
                "subcategory": "Cream Concealer",
                "finish": "Radiant Natural",
                "price": 32.00,
                "description": "Multi-action concealer that obscures imperfections, blurs lines, and leaves a radiant skin finish.",
                "image_url": "https://images.unsplash.com/photo-1599733589046-10c005739ef9?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Chantilly", "L1", "#F4E5D4", "neutral", "Fair with subtle neutral undertone"),
                    ("Vanilla", "L2", "#ECD3BD", "cool", "Fair-light with tiny pink cast"),
                    ("Custard", "M1", "#DFB78B", "warm", "Medium with warm golden undertone"),
                    ("Caramel", "M2", "#B88258", "warm", "Medium-dark with rich golden peach undertones"),
                    ("Amande", "D1", "#784B31", "neutral", "Deep with balanced golden olive warmth")
                ]
            },
            # Blush
            {
                "brand": "rare-beauty",
                "category": "blush",
                "name": "Soft Pinch Liquid Blush",
                "subcategory": "Liquid Blush",
                "finish": "Dewy Radiant",
                "price": 23.00,
                "description": "Weightless, long-lasting liquid blush that blends and builds beautifully for a soft, healthy flush.",
                "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Hope", "HP", "#D67D78", "neutral-warm", "Nude mauve dewy flush"),
                    ("Happy", "HY", "#E66885", "cool", "Dewy cool bubblegum pink"),
                    ("Joy", "JY", "#E8765A", "warm", "Dewy muted peach coral"),
                    ("Bliss", "BL", "#DB8E83", "neutral", "Soft matte rose peach"),
                    ("Grateful", "GR", "#C8263A", "neutral-cool", "True red dewy radiance")
                ]
            },
            # Bronzer
            {
                "brand": "fenty-beauty",
                "category": "bronzer",
                "name": "Cheeks Out Freestyle Cream Bronzer",
                "subcategory": "Cream Bronzer",
                "finish": "Natural Sheen",
                "price": 35.00,
                "description": "Non-greasy cream bronzer that effortlessly melts into skin for a natural-looking sun-soaked bronze.",
                "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Amber", "01", "#8C6A5A", "cool", "Cool contour taupe for fair to medium skin"),
                    ("Butta Biscuit", "02", "#9E6D4E", "warm", "Warm light bronze"),
                    ("Macchiato", "03", "#7D4F36", "warm", "Medium bronze with golden warmth"),
                    ("Toffee Tease", "05", "#553424", "neutral", "Deep chocolate bronze")
                ]
            },
            # Highlighter
            {
                "brand": "charlotte-tilbury",
                "category": "highlighter",
                "name": "Beauty Light Wand",
                "subcategory": "Liquid Highlighter",
                "finish": "Glow Luminous",
                "price": 42.00,
                "description": "Iconic rose gold and champagne liquid highlighter that gives a soft-focus candlelight glow.",
                "image_url": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Spotlight", "SP", "#F3E3CF", "neutral-warm", "Rose gold champagne candlelit gleam"),
                    ("Pinkgasm", "PG", "#E5777D", "neutral", "Luminous pearlescent rose pink"),
                    ("Peachgasm", "PC", "#E6917A", "warm", "Peach champagne sunset glow"),
                    ("Goldgasm", "GG", "#E2B871", "warm", "Molten golden halo")
                ]
            },
            # Eyeshadow
            {
                "brand": "mac",
                "category": "eyeshadow",
                "name": "Connect In Colour Eye Shadow Palette",
                "subcategory": "Powder Eyeshadow",
                "finish": "Satin & Shimmer",
                "price": 44.00,
                "description": "Pigment-packed eyeshadow quad delivering high-impact color with silky seamless blendability.",
                "image_url": "https://images.unsplash.com/photo-1583241800698-e8ab01830a07?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Bronze Ambition", "BA", "#946B4E", "warm", "Golden bronze, champagne gold, and warm amber taupe"),
                    ("Rose Romance", "RR", "#B97A81", "neutral-cool", "Velvet dusty rose, plum taupe, and icy gleam"),
                    ("Nude Model", "NM", "#937B72", "neutral", "Soft camel, mocha brown, and satin ivory")
                ]
            },
            # Eyeliner
            {
                "brand": "fenty-beauty",
                "category": "eyeliner",
                "name": "Flyliner Longwear Liquid Eyeliner",
                "subcategory": "Felt-Tip Liquid Liner",
                "finish": "Satin Matte",
                "price": 24.00,
                "description": "Hyper-saturated water-resistant liquid eyeliner with an innovative flex tip for crisp wings.",
                "image_url": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Cuz I'm Black", "01", "#151515", "neutral", "True intense black satin"),
                    ("In Big Truffle", "02", "#352723", "neutral-warm", "Rich chocolate espresso brown")
                ]
            },
            # Mascara
            {
                "brand": "maybelline",
                "category": "mascara",
                "name": "Lash Sensational Sky High Mascara",
                "subcategory": "Lengthening Mascara",
                "finish": "Glossy Flexible",
                "price": 12.99,
                "description": "Exclusive Flex Tower brush bends to volumize and extend every single lash from root to tip.",
                "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Very Black", "801", "#111111", "neutral", "Intense carbon black"),
                    ("True Brown", "803", "#2C1E18", "neutral-warm", "Soft natural black-brown")
                ]
            },
            # Brows
            {
                "brand": "glossier",
                "category": "brows",
                "name": "Boy Brow Fluffing Pomade",
                "subcategory": "Tinted Brow Gel",
                "finish": "Flexible Satin",
                "price": 20.00,
                "description": "Brushable, flexible wax pomade that visibly thickens, shapes, and grooms brows into place.",
                "image_url": "https://images.unsplash.com/photo-1583241800698-e8ab01830a07?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Clear", "CL", "#FFFFFF", "neutral", "Invisible flexible hold"),
                    ("Blonde", "BL", "#A48E75", "neutral-warm", "Soft honey blonde taupe"),
                    ("Brown", "BR", "#544437", "neutral-warm", "Warm chocolate chestnut brown"),
                    ("Black", "BK", "#231F1D", "neutral", "Soft black for deep hair")
                ]
            },
            # Lips
            {
                "brand": "mac",
                "category": "lips",
                "name": "Retro Matte Lipstick",
                "subcategory": "Matte Lipstick",
                "finish": "Velvet Matte",
                "price": 23.00,
                "description": "The iconic lipstick that made MAC famous with a long-wearing, non-feathering matte finish.",
                "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Velvet Teddy", "617", "#B57B6C", "neutral-warm", "Deep-tone beige nude"),
                    ("Ruby Woo", "707", "#BA1E29", "cool", "Very matte vivid blue-red"),
                    ("Whirl", "626", "#8F5E51", "neutral", "Dirty rose taupe"),
                    ("Mehr", "608", "#B06B78", "cool", "Dirty blue-pink mauve"),
                    ("Chili", "602", "#A63D2E", "warm", "Warm brownish-orange red")
                ]
            },
            {
                "brand": "rare-beauty",
                "category": "lips",
                "name": "Kind Words Matte Lipstick",
                "subcategory": "Comfort Matte Lipstick",
                "finish": "Buttery Satin Matte",
                "price": 20.00,
                "description": "Buttery, non-drying lipstick that hugs lips in pure color and a cushiony, comfortable feel.",
                "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Humble", "HM", "#C98579", "neutral-warm", "Muted rose mauve"),
                    ("Creative", "CR", "#AF6154", "warm", "Muted terracotta peach"),
                    ("Worthy", "WO", "#A45B5B", "neutral", "Muted soft plum rose"),
                    ("Bold", "BD", "#6C3138", "neutral-cool", "Deep berry mahogany")
                ]
            },
            # Setting
            {
                "brand": "laura-mercier",
                "category": "setting",
                "name": "Translucent Loose Setting Powder",
                "subcategory": "Setting Powder",
                "finish": "Weightless Matte",
                "price": 43.00,
                "description": "Cult-favorite, lightweight loose powder that sets makeup flawlessly for 16-hour matte wear without flashback.",
                "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=500&auto=format&fit=crop&q=60",
                "shades": [
                    ("Translucent", "01", "#FBF5EB", "neutral", "Fair to medium skin tones"),
                    ("Honey", "02", "#ECCAA1", "warm", "Medium skintones with olive and golden undertones"),
                    ("Medium Deep", "03", "#9B6C4B", "warm", "Deep to very deep skintones")
                ]
            }
        ]

        created_count = 0
        shades_count = 0

        for p_info in products_data:
            brand = brand_map[p_info["brand"]]
            cat = cat_map[p_info["category"]]
            product, p_created = Product.objects.get_or_create(
                brand=brand,
                name=p_info["name"],
                defaults={
                    "category": cat,
                    "subcategory": p_info.get("subcategory", ""),
                    "finish": p_info.get("finish", ""),
                    "price": p_info.get("price"),
                    "description": p_info.get("description", ""),
                    "image_url": p_info.get("image_url", ""),
                }
            )
            if p_created:
                created_count += 1

            for s_name, s_code, s_hex, s_under, s_desc in p_info.get("shades", []):
                shade, s_created = ProductShade.objects.get_or_create(
                    product=product,
                    name=s_name,
                    defaults={
                        "shade_code": s_code,
                        "hex_color": s_hex,
                        "undertone": s_under,
                        "description": s_desc
                    }
                )
                if s_created:
                    shades_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(categories_data)} categories, {len(brands_data)} brands, "
            f"{created_count} products, and {shades_count} shades!"
        ))
