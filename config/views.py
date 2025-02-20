from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, renderer_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
import csv
import io
import json
from .models import Certificate, CertificateField
from .serializers import CertificateSerializer, CertificateFieldSerializer
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

# Add these renderers to your views
class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Customize the rendering if needed
        return super().render(data, accepted_media_type, renderer_context)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_certificate(request):
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('csv_file')
            template = request.FILES.get('template')
            title = request.POST.get('title')
            organization = request.POST.get('organization')
            roll_column = request.POST.get('roll_column')
            user = request.POST.get('user')
            variables = request.POST.get('variables')

            if not all([csv_file, template, title, organization, roll_column, user, variables]):
                return Response(
                    {'error': 'Missing required fields'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            certificate = Certificate.objects.create(
            title=title, 
                organization=organization,
            user=user, 
            template=template, 
                csv_data=csv_file,
                roll_column=roll_column
        )

            variables = json.loads(variables)

            for variable in variables:
                CertificateField.objects.create(
                    certificate=certificate, 
                    field_name=variable['field_name'], 
                    csv_column=variable['csv_column'],
                    x=variable['x'], 
                    y=variable['y'], 
                    font_size=variable['font_size'], 
                    font_color=variable['font_color'], 
                    font_family=variable['font_family']
                )
            
            return Response({'id': certificate.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Error:", e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['DELETE'])
def delete_certificate(request, pk, user):
    try:
        certificate = Certificate.objects.get(id=pk, user=user)
        certificate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Certificate.DoesNotExist:
        return Response(
            {"error": "Certificate not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print("Error deleting certificate:", str(e))
        return Response(
            {"error": "Failed to delete certificate"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def user_certificate_list(request, user):
    try:
        certificates = Certificate.objects.filter(user=user)
        serializer = CertificateSerializer(certificates, many=True)
        return Response(serializer.data)
    except Exception as e:
        print("Error in user_certificate_list:", str(e))
        return Response(
            {"error": "Failed to fetch certificates"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    
@api_view(['GET'])
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def certificate_list(request):
    if request.method == 'GET':
        certificates = Certificate.objects.filter(verified=True)
        serializer = CertificateSerializer(certificates, many=True)
        return Response(serializer.data)
    
def certificate_detail(request, certificate_id, roll_no):
    if request.method == 'GET':
        certificate = Certificate.objects.get(id=certificate_id)
        csv = certificate.csv_data
        df = pd.read_csv(csv)
        filtered_df = df[df['roll_no'] == roll_no]
        if filtered_df.empty:
            return Response({'error': 'Roll number not found'}, status=status.HTTP_404_NOT_FOUND)
        row = filtered_df.iloc[0]

        variables = CertificateField.objects.filter(certificate=certificate)
        data = {}
        for variable in variables:
            data[variable.field_name] = row[variable.field_name]
        return Response(data)
    
@api_view(['GET'])
def certificate_preview(request, pk):
    try:
        certificate = Certificate.objects.get(id=pk)
        fields = CertificateField.objects.filter(certificate=certificate)
        
        # Read first row of CSV
        df = pd.read_csv(certificate.csv_data)
        first_row = df.iloc[0].to_dict()
        
        # Create fields dictionary with field_name as key
        fields_serializer = CertificateFieldSerializer(fields, many=True)
        certificate_serializer = CertificateSerializer(certificate)
        
        # Map field data to their positions and styles
        field_data = {}
        for field in fields:
            # Get the value from CSV using csv_column instead of field_name
            csv_value = first_row.get(field.csv_column)
            if csv_value is not None:
                field_data[field.field_name] = {
                    'value': str(csv_value),
                    'x': field.x,
                    'y': field.y,
                    'font_size': field.font_size,
                    'font_color': field.font_color,
                    'font_family': field.font_family
                }
        return Response({
            'template': certificate_serializer.data['template'],
            'fields': field_data
        })
    except Exception as e:
        print("Error in certificate_preview:", str(e))
        return Response(
            {"error": "Failed to fetch preview"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'DELETE'])
def user_templates(request, user):
    if request.method == 'GET':
        try:
            certificates = Certificate.objects.filter(user=user)
            templates_data = []
            
            for cert in certificates:
                template_data = {
                    'id': cert.id,
                    'title': cert.title,
                    'template': cert.template.url,
                    'verified': cert.verified,
                    'organization': cert.organization,
                    'created_at': cert.created_at,
                    'csv_data': cert.csv_data.url,
                    'fields': []
                }
                
                fields = CertificateField.objects.filter(certificate=cert)
                for field in fields:
                    template_data['fields'].append({
                        'field_name': field.field_name,
                        'x': field.x,
                        'y': field.y,
                        'font_size': field.font_size,
                        'font_color': field.font_color,
                        'font_family': field.font_family
                    })
                
                templates_data.append(template_data)
            
            # Explicitly set the renderer
            renderer = CustomRenderer()
            rendered_content = renderer.render(templates_data)
            
            return Response(templates_data)
        except Exception as e:
            print("Error fetching templates:", str(e))
            return Response(
                {"error": "Failed to fetch templates"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def certificate_details(request, pk, roll_no):
    try:
        certificate = Certificate.objects.get(id=pk)
        fields = CertificateField.objects.filter(certificate=certificate)
        
        # Read CSV and find the row with matching roll number
        df = pd.read_csv(certificate.csv_data)
        filtered_df = df[df[certificate.roll_column] == roll_no]
        
        if filtered_df.empty:
            return Response(
                {"error": "Roll number not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        row = filtered_df.iloc[0].to_dict()
        
        # Map field data to their positions and styles
        field_data = {}
        for field in fields:
            csv_value = row.get(field.csv_column)
            if csv_value is not None:
                field_data[field.field_name] = {
                    'value': str(csv_value),
                    'x': field.x,
                    'y': field.y,
                    'font_size': field.font_size,
                    'font_color': field.font_color,
                    'font_family': field.font_family
                }

        return Response({
            'template': certificate.template.url,
            'title': certificate.title,
            'organization': certificate.organization,
            'fields': field_data
        })
    except Certificate.DoesNotExist:
        return Response(
            {"error": "Certificate not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print("Error in certificate_details:", str(e))
        return Response(
            {"error": "Failed to fetch certificate details"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def certificate_info(request, pk):
    try:
        certificate = Certificate.objects.get(id=pk)
        return Response({
            'title': certificate.title,
            'organization': certificate.organization
        })
    except Certificate.DoesNotExist:
        return Response(
            {"error": "Certificate not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@renderer_classes([JSONRenderer, BrowsableAPIRenderer])
def generate_certificate(request, pk, roll_no, mode='preview'):
    try:
        certificate = Certificate.objects.get(id=pk)
        fields = CertificateField.objects.filter(certificate=certificate)
        
        # Read CSV and find the row with matching roll number
        df = pd.read_csv(certificate.csv_data)
        filtered_df = df[df[certificate.roll_column] == roll_no]
        
        if filtered_df.empty:
            return Response(
                {"error": "Roll number not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        row = filtered_df.iloc[0].to_dict()
        
        # Open the template image
        with certificate.template.open('rb') as template_file:
            img = Image.open(template_file)
            draw = ImageDraw.Draw(img)
            
            # Get image dimensions
            img_width, img_height = img.size
            
            # Add text for each field
            for field in fields:
                try:
                    csv_value = str(row.get(field.csv_column, ''))
                    
                    # Create font with specified size
                    try:
                        # Try to use TrueType font with specified size
                        font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                            size=field.font_size
                        )
                    except:
                        # If TrueType fails, create basic font with size
                        font = ImageFont.load_default()
                        # Scale up the default font
                        font_size = field.font_size
                        if font_size > 20:  # Default font is small, scale it up
                            font = ImageFont.truetype(
                                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                size=font_size
                            )
                    
                    # Simple positioning - use the coordinates directly
                    x = field.x
                    y = field.y
                    
                    # Draw text
                    draw.text(
                        (x, y),
                        csv_value,
                        font=font,
                        fill=field.font_color or 'black',
                    )
                    
                    print(f"Added text: {csv_value} at position ({x}, {y}) with size {field.font_size}")
                    
                except Exception as e:
                    print(f"Error adding text for field {field.field_name}: {str(e)}")
                    continue
            
            # Save the image
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format='PNG')
            img_byte_array.seek(0)
            
            # Return the response
            response = HttpResponse(img_byte_array.getvalue(), content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="certificate_{pk}_{roll_no}.png"'
            return response
            
    except Exception as e:
        print(f"Certificate generation error: {str(e)}")
        return Response(
            {"error": "Failed to generate certificate"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def download_csv(request, pk, user):
    try:
        certificate = Certificate.objects.get(id=pk, user=user)
        
        # Open the CSV file
        with open(certificate.csv_data.path, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{certificate.title.lower().replace(" ", "-")}-data.csv"'
            return response
            
    except Certificate.DoesNotExist:
        return Response(
            {"error": "Certificate not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print("Error downloading CSV:", str(e))
        return Response(
            {"error": "Failed to download CSV"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
