import os
import boto3
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.http import require_GET


def health(request):
    return JsonResponse({"ok": True})


@require_GET
def media_proxy(request, key: str):
    """
    Редиректит на подписанный URL из Cloudflare R2 (S3-совместимо).
    Пример: /content/media/images/avatars/peer_avatar_1.jpg
    """
    bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME")
    endpoint = os.environ.get("AWS_S3_ENDPOINT_URL") 
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    r2_public_url = os.environ.get("R2_PUBLIC_URL")
    expires = int(os.environ.get("R2_SIGNED_URL_TTL", "3600"))

    # Temporary fallback: if R2_PUBLIC_URL is available, try direct access first
    # This is a workaround for production deployment issues
    if r2_public_url and not all([bucket, endpoint, access_key, secret_key]):
        direct_url = f"{r2_public_url.rstrip('/')}/{key}"
        return HttpResponseRedirect(direct_url)

    if not all([bucket, endpoint, access_key, secret_key]):
        return HttpResponseBadRequest("R2 env vars are not configured")

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )

        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires,
        )
        return HttpResponseRedirect(url)
    except Exception as e:
        # Fallback to direct R2 URL if signing fails
        if r2_public_url:
            direct_url = f"{r2_public_url.rstrip('/')}/{key}"
            return HttpResponseRedirect(direct_url)
        return HttpResponseBadRequest(f"Failed to generate signed URL: {str(e)}")