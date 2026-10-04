from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.http import urlencode
from django.views import View

from apps.accounts.mixins import PortalRequiredMixin
from apps.common.choices import InstrumentSection
from apps.musicians.selectors import profile_for

from . import selectors, services


class PieceListView(PortalRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        section = request.GET.get("sekce", "")
        if section not in InstrumentSection.values:
            section = ""
        query = request.GET.get("q", "").strip()[:100]
        page = Paginator(selectors.visible_pieces(query=query, section=section), 25).get_page(
            request.GET.get("strana")
        )
        profile = profile_for(request.user)
        return render(
            request,
            "sheet_music/list.html",
            {
                "page": page,
                "query": query,
                "section": section,
                "sections": InstrumentSection.choices,
                "own_section": profile.section if profile else "",
                "extra_query": urlencode({"sekce": section, "q": query}),
            },
        )


class PartDownloadView(PortalRequiredMixin, View):
    """Authorization: portal permission + object visibility. Files have no public URL."""

    http_method_names = ["get"]

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        part = selectors.downloadable_part(pk)
        if part is None:
            raise Http404
        try:
            handle = part.file.open("rb")
        except FileNotFoundError:
            raise Http404 from None
        services.log_download(part, request.user)
        response = FileResponse(
            handle,
            as_attachment=True,
            filename=services.download_filename(part),
            content_type="application/pdf",
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Robots-Tag"] = "noindex, noarchive"
        return response
