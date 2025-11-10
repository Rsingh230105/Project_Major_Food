class VideoUploadView(TemplateView):
    """View for uploading video content"""
    template_name = 'detector/media/video_upload.html'

    def post(self, request, *args, **kwargs):
        # Handle video upload
        video_file = request.FILES.get('video')
        if video_file:
            # Process video file
            return redirect('detector:upload_video')
        return self.get(request, *args, **kwargs)


class ImagesUploadView(TemplateView):
    """View for uploading multiple images"""
    template_name = 'detector/media/images_upload.html'

    def post(self, request, *args, **kwargs):
        # Handle multiple image upload
        images = request.FILES.getlist('images')
        if images:
            # Process images
            return redirect('detector:upload_images')
        return self.get(request, *args, **kwargs)


class AdsUploadView(TemplateView):
    """View for uploading advertisements"""
    template_name = 'detector/media/ads_upload.html'

    def post(self, request, *args, **kwargs):
        # Handle advertisement upload
        ad_content = request.FILES.get('ad')
        if ad_content:
            # Process advertisement
            return redirect('detector:upload_ads')
        return self.get(request, *args, **kwargs)