"""Placeholder text shown until editors fill in real content. No invented facts."""

DEFAULT_PAGES: dict[str, tuple[str, str, str]] = {
    # key: (title, intro, body)
    "home-hero": (
        "Dechová hudba Oderské chasy",
        "Tradiční dechová hudba pro slavnosti, plesy i obecní oslavy.",
        "",
    ),
    "home-intro": (
        "Vítejte",
        "",
        "[Doplní provozovatel] Krátké představení kapely, jejího repertoáru a toho, "
        "pro koho hraje.",
    ),
    "about-history": (
        "Historie kapely",
        "[Rok založení bude doplněn]",
        "[Doplní provozovatel] Zde bude příběh kapely. Text zatím nebyl dodán.",
    ),
    "about-style": (
        "Hudební styl",
        "",
        "[Doplní provozovatel] Popis repertoáru: dechovka, moravské a valašské písně, "
        "polky, valčíky a pochody.",
    ),
    "about-current": (
        "Kapela dnes",
        "",
        "[Doplní provozovatel] Popis současného složení a fungování kapely.",
    ),
    "ochrana-osobnich-udaju": (
        "Ochrana osobních údajů",
        "",
        "[Vyžaduje právní kontrolu provozovatelem] Zde bude zásada ochrany osobních údajů: "
        "správce, účely, právní základy, doby uchování a práva subjektů údajů. "
        "Technické podklady jsou v dokumentaci projektu.",
    ),
    "cookies": (
        "Cookies",
        "Web používá pouze nezbytné cookies.",
        "Používáme výhradně technicky nezbytné cookies: relace přihlášení (sessionid) a "
        "ochranu formulářů proti zneužití (csrftoken). Tyto cookies nevyžadují souhlas a "
        "neslouží ke sledování. Web nepoužívá analytické, marketingové ani jiné "
        "nepovinné cookies. Pokud je v budoucnu zavedeme, budou vypnuté, dokud nebude "
        "udělen výslovný souhlas.\n\n[Vyžaduje kontrolu provozovatelem]",
    ),
    "provozovatel": (
        "Provozovatel webu",
        "",
        "[Doplní provozovatel] Název, sídlo, IČO a kontaktní údaje provozovatele.",
    ),
    "prohlaseni-o-pristupnosti": (
        "Prohlášení o přístupnosti",
        "",
        "Cílem webu je splnit požadavky WCAG 2.2 úrovně AA. Soulad zatím nebyl "
        "nezávisle ověřen; automatizované i ruční kontroly probíhají v rámci vývoje. "
        "Narazíte-li na překážku, napište na kontakt uvedený níže.\n\n"
        "[Vyžaduje kontrolu provozovatelem]",
    ),
    "bezpecnost": (
        "Bezpečnostní kontakt",
        "",
        "Zranitelnost webu nahlaste na bezpečnostní kontakt uvedený níže. "
        "Prosíme o zdrženlivost: neprocházejte cizí data a dejte nám čas na opravu.",
    ),
    "odstraneni-fotografie": (
        "Odstranění fotografie",
        "",
        "Pokud se na fotografii poznáváte a nechcete, aby byla zveřejněna, napište na "
        "kontakt pro ochranu osobních údajů a uveďte, o kterou fotografii jde (odkaz na "
        "album a popis). Fotografii bez zbytečného odkladu skryjeme.\n\n"
        "[Vyžaduje právní kontrolu provozovatelem]",
    ),
}
