from django.contrib import admin
from .models import TestValores, ParteTest, PreguntaValores, OpcionValores
from django.utils.html import format_html
from .models import TestDomino, ProblemaDomino, ResultadoDomino
import json

admin.site.register(TestValores)
admin.site.register(ParteTest)
admin.site.register(PreguntaValores)
admin.site.register(OpcionValores)

class ProblemaDominoInline(admin.TabularInline):
    model = ProblemaDomino
    extra = 0
    fields = [
        'numero', 
        'tipo', 
        'matriz_filas', 
        'matriz_columnas', 
        'fichas_display', 
        'respuesta'
    ]
    readonly_fields = ['fichas_display']
    
    def fichas_display(self, obj):
        return format_html("<pre>{}</pre>", json.dumps(obj.fichas, indent=2))
    fichas_display.short_description = "Fichas"

@admin.register(TestDomino)
class TestDominoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_disposicion', 'tiempo_limite']
    list_filter = ['tipo_disposicion']
    inlines = [ProblemaDominoInline]
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'tiempo_limite', 'tipo_disposicion')
        }),
        ('Instrucciones', {
            'fields': ('instrucciones',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProblemaDomino)
class ProblemaDominoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'test', 'tipo', 'matriz_info']
    list_filter = ['test', 'tipo']
    search_fields = ['numero', 'test__nombre']
    
    fieldsets = (
        (None, {
            'fields': ('test', 'numero', 'tipo')
        }),
        ('Configuración Matricial', {
            'fields': ('matriz_filas', 'matriz_columnas'),
            'classes': ('collapse',)
        }),
        ('Fichas y Respuesta', {
            'fields': ('fichas', 'respuesta')
        }),
        ('Configuración Especial', {
            'fields': ('configuracion_extra',),
            'classes': ('collapse',)
        }),
    )
    
    def matriz_info(self, obj):
        if obj.tipo == 'MATRIZ':
            return f"{obj.matriz_filas}x{obj.matriz_columnas}"
        return "-"
    matriz_info.short_description = "Matriz"

@admin.register(ResultadoDomino)
class ResultadoDominoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'test', 'fecha', 'puntuacion', 'percentil', 'tiempo_utilizado']
    list_filter = ['test', 'fecha']
    search_fields = ['usuario__username', 'test__nombre']
    readonly_fields = ['fecha', 'respuestas_display']
    
    fieldsets = (
        (None, {
            'fields': ('usuario', 'test', 'fecha')
        }),
        ('Resultados', {
            'fields': ('puntuacion', 'percentil', 'tiempo_utilizado')
        }),
        ('Respuestas', {
            'fields': ('respuestas_display',),
            'classes': ('collapse',)
        }),
    )
    
    def respuestas_display(self, obj):
        return format_html("<pre>{}</pre>", json.dumps(obj.respuestas, indent=2))
    respuestas_display.short_description = "Respuestas Detalladas"