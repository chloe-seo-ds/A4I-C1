"""
Response Formatter for Education Insights
Generates rich responses with:
- Executive summaries with direct answers
- Data visualizations (charts & graphs)
- Google Maps integration for school locations
"""

import os
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO


def format_response_with_visualizations(
    query: str,
    data: List[Dict[str, Any]],
    query_type: str,
    maps_api_key: Optional[str] = None,
    state_averages: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a response with executive summary, charts, and maps.
    
    Args:
        query: Original user query
        data: List of school data dictionaries
        query_type: Type of query (high_need_low_tech, high_grad_low_funding, stem_excellence)
        maps_api_key: Google Maps API key for map rendering
        state_averages: State-wide averages for comparison
        
    Returns:
        Dictionary with formatted response components
    """
    if not data:
        return {
            "summary": "No schools found matching your criteria.",
            "chart_html": None,
            "map_html": None,
            "full_response": "No schools found matching your criteria."
        }
    
    # Generate executive summary
    summary = _generate_executive_summary(data, query_type)
    
    # Skip charts - only generate map
    chart_html = None
    
    # Generate map
    map_html = _generate_map(data, maps_api_key) if maps_api_key else None
    
    # Combine into full response
    full_response = _combine_response_components(summary, chart_html, map_html, data, query_type)
    
    return {
        "summary": summary,
        "chart_html": chart_html,
        "map_html": map_html,
        "full_response": full_response,
        "school_count": len(data)
    }


def _generate_executive_summary(data: List[Dict[str, Any]], query_type: str) -> str:
    """Generate a concise executive summary with direct answers."""
    
    summary_html = []
    summary_html.append('<div style="background: linear-gradient(to right, #eff6ff, #f0f9ff); padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 20px;">')
    
    if query_type == "high_need_low_tech":
        # For grant priority schools
        summary_html.append('<h2 style="color: #1e40af; margin: 0 0 15px 0; font-size: 1.3rem;">🎯 Executive Summary</h2>')
        summary_html.append(f'<p style="color: #1e3a8a; font-size: 1.05rem; margin-bottom: 15px;"><strong>Found {len(data)} schools requiring priority grant funding:</strong></p>')
        summary_html.append('<ol style="color: #1f2937; line-height: 1.8; margin: 0; padding-left: 20px;">')
        
        for i, school in enumerate(data[:5], 1):
            summary_html.append(
                f'<li><strong>{school["school_name"]}</strong> ({school["city_location"]}) - '
                f'{school["low_income_pct"]}% low-income students, '
                f'${int(school["per_pupil_total"]):,} per-pupil spending</li>'
            )
        
    elif query_type == "high_grad_low_funding":
        # For high-performing despite challenges
        summary_html.append('<h2 style="color: #92400e; margin: 0 0 15px 0; font-size: 1.3rem;">⭐ Executive Summary</h2>')
        summary_html.append(f'<p style="color: #78350f; font-size: 1.05rem; margin-bottom: 15px;"><strong>Found {len(data)} high-performing schools despite funding challenges:</strong></p>')
        summary_html.append('<ol style="color: #1f2937; line-height: 1.8; margin: 0; padding-left: 20px;">')
        
        for i, school in enumerate(data[:5], 1):
            summary_html.append(
                f'<li><strong>{school["school_name"]}</strong> ({school["city_location"]}) - '
                f'{school["graduation_rate"]}% graduation rate, '
                f'{school["low_income_pct"]}% low-income</li>'
            )
    
    elif query_type == "stem_excellence":
        # For STEM programs with small classes
        summary_html.append('<h2 style="color: #6b21a8; margin: 0 0 15px 0; font-size: 1.3rem;">🔬 Executive Summary</h2>')
        summary_html.append(f'<p style="color: #581c87; font-size: 1.05rem; margin-bottom: 15px;"><strong>Found {len(data)} schools with strong STEM programs and favorable class sizes:</strong></p>')
        summary_html.append('<ol style="color: #1f2937; line-height: 1.8; margin: 0; padding-left: 20px;">')
        
        for i, school in enumerate(data[:5], 1):
            ap_courses = school.get('ap_courses', 0) or 0
            summary_html.append(
                f'<li><strong>{school["school_name"]}</strong> ({school["city_location"]}) - '
                f'{ap_courses} AP courses, '
                f'{school["student_teacher_ratio"]} student-teacher ratio</li>'
            )
    
    else:
        summary_html.append(f'<h2 style="color: #1f2937; margin: 0 0 15px 0;">📊 Executive Summary</h2>')
        summary_html.append(f'<p><strong>Found {len(data)} schools</strong></p>')
    
    summary_html.append('</ol>')
    summary_html.append('</div>')
    
    return '\n'.join(summary_html)


def _generate_charts(data: List[Dict[str, Any]], query_type: str, state_averages: Optional[Dict[str, Any]] = None) -> str:
    """Generate HTML charts using Chart.js (via CDN)."""
    
    if not data:
        return ""
    
    # Extract data for charts based on query type
    school_names = [school.get('school_name', 'Unknown')[:30] for school in data[:10]]
    
    charts_html = []
    charts_html.append('<div class="charts-container" style="margin: 20px 0;">')
    
    if query_type == "high_need_low_tech":
        # Chart 1: Low-income percentage with state average
        low_income_pcts = [school.get('low_income_pct', 0) for school in data[:10]]
        state_avg_low_income = state_averages.get('avg_low_income_pct', 0) if state_averages else 0
        
        # Chart 2: Per-pupil spending with state average
        spending = [school.get('per_pupil_total', 0) for school in data[:10]]
        state_avg_spending = state_averages.get('avg_per_pupil_spending', 0) if state_averages else 0
        
        charts_html.append(_create_comparison_bar_chart(
            chart_id="lowIncomeChart",
            title="Low-Income Student Percentage (vs CA Average)",
            labels=school_names,
            data=low_income_pcts,
            state_average=state_avg_low_income,
            color='rgba(239, 68, 68, 0.8)',
            ylabel='Percentage (%)'
        ))
        
        charts_html.append(_create_comparison_bar_chart(
            chart_id="spendingChart",
            title="Per-Pupil Spending (vs CA Average)",
            labels=school_names,
            data=spending,
            state_average=state_avg_spending,
            color='rgba(59, 130, 246, 0.8)',
            ylabel='Dollars ($)'
        ))
    
    elif query_type == "high_grad_low_funding":
        # Chart 1: Graduation rates with state average
        grad_rates = [school.get('graduation_rate', 0) for school in data[:10]]
        state_avg_grad = state_averages.get('avg_graduation_rate', 0) if state_averages else 0
        
        # Chart 2: Low-income percentage with state average
        low_income_pcts = [school.get('low_income_pct', 0) for school in data[:10]]
        state_avg_low_income = state_averages.get('avg_low_income_pct', 0) if state_averages else 0
        
        charts_html.append(_create_comparison_bar_chart(
            chart_id="gradRateChart",
            title="Graduation Rates (vs CA Average)",
            labels=school_names,
            data=grad_rates,
            state_average=state_avg_grad,
            color='rgba(34, 197, 94, 0.8)',
            ylabel='Percentage (%)'
        ))
        
        charts_html.append(_create_comparison_bar_chart(
            chart_id="lowIncomeChart2",
            title="Low-Income Student Percentage (vs CA Average)",
            labels=school_names,
            data=low_income_pcts,
            state_average=state_avg_low_income,
            color='rgba(251, 146, 60, 0.8)',
            ylabel='Percentage (%)'
        ))
    
    elif query_type == "stem_excellence":
        # Chart 1: AP courses offered (no state average available for this)
        ap_courses = [school.get('ap_courses', 0) or 0 for school in data[:10]]
        
        # Chart 2: Student-teacher ratio with state average
        ratios = [school.get('student_teacher_ratio', 0) for school in data[:10]]
        state_avg_ratio = state_averages.get('avg_student_teacher_ratio', 0) if state_averages else 0
        
        charts_html.append(_create_bar_chart(
            chart_id="apCoursesChart",
            title="AP Courses Offered",
            labels=school_names,
            data=ap_courses,
            color='rgba(168, 85, 247, 0.8)',
            ylabel='Number of Courses'
        ))
        
        charts_html.append(_create_comparison_bar_chart(
            chart_id="ratioChart",
            title="Student-Teacher Ratio (vs CA Average)",
            labels=school_names,
            data=ratios,
            state_average=state_avg_ratio,
            color='rgba(20, 184, 166, 0.8)',
            ylabel='Ratio'
        ))
    
    charts_html.append('</div>')
    
    return '\n'.join(charts_html)


def _create_comparison_bar_chart(chart_id: str, title: str, labels: List[str], 
                                data: List[float], state_average: float, color: str, ylabel: str) -> str:
    """Create a bar chart with state average comparison line using Chart.js."""
    
    # Convert to JSON properly
    import json
    import html
    
    # Create array of state average for line
    state_avg_array = [state_average] * len(data)
    
    # Create chart config
    chart_config = {
        "type": "bar",
        "labels": labels,
        "datasets": [
            {
                "label": "Selected Schools",
                "data": data,
                "backgroundColor": color,
                "borderColor": color.replace("0.8", "1"),
                "borderWidth": 2,
                "borderRadius": 6,
                "type": "bar"
            },
            {
                "label": "CA State Average",
                "data": state_avg_array,
                "borderColor": "rgba(107, 114, 128, 1)",
                "backgroundColor": "rgba(107, 114, 128, 0.1)",
                "borderWidth": 3,
                "borderDash": [5, 5],
                "pointRadius": 0,
                "type": "line",
                "fill": False
            }
        ],
        "ylabel": ylabel
    }
    
    chart_config_json = html.escape(json.dumps(chart_config))
    
    return f'''
<div class="chart-wrapper" style="background: white; padding: 20px; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 1.1rem;">{title}</h3>
    <canvas id="{chart_id}" class="chart-canvas" data-chart-config="{chart_config_json}" style="max-height: 300px; height: 300px;"></canvas>
</div>
'''


def _create_bar_chart(chart_id: str, title: str, labels: List[str], 
                     data: List[float], color: str, ylabel: str) -> str:
    """Create a single bar chart using Chart.js."""
    
    # Convert to JSON properly
    import json
    import html
    
    chart_config = {
        "type": "bar",
        "labels": labels,
        "datasets": [{
            "label": ylabel,
            "data": data,
            "backgroundColor": color,
            "borderColor": color.replace("0.8", "1"),
            "borderWidth": 2,
            "borderRadius": 6
        }],
        "ylabel": ylabel
    }
    
    chart_config_json = html.escape(json.dumps(chart_config))
    
    return f'''
<div class="chart-wrapper" style="background: white; padding: 20px; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 1.1rem;">{title}</h3>
    <canvas id="{chart_id}" class="chart-canvas" data-chart-config="{chart_config_json}" style="max-height: 300px; height: 300px;"></canvas>
</div>
'''


def _generate_map(data: List[Dict[str, Any]], maps_api_key: str) -> str:
    """Generate Google Maps HTML with school markers."""
    import json
    import html
    
    # Filter schools with valid coordinates
    schools_with_coords = [
        school for school in data 
        if school.get('latitude') and school.get('longitude')
    ]
    
    if not schools_with_coords:
        return '<div style="padding: 20px; background: #fef3c7; border-radius: 8px; color: #92400e;">⚠️ Location data not available for these schools.</div>'
    
    # Calculate center point (average of all coordinates)
    avg_lat = sum(float(s['latitude']) for s in schools_with_coords) / len(schools_with_coords)
    avg_lng = sum(float(s['longitude']) for s in schools_with_coords) / len(schools_with_coords)
    
    # Generate markers data
    markers_data = []
    for i, school in enumerate(schools_with_coords[:20], 1):  # Limit to 20 markers
        lat = float(school['latitude'])
        lng = float(school['longitude'])
        name = school.get('school_name', 'Unknown School')
        city = school.get('city_location', 'Unknown')
        enrollment = school.get('enrollment', 'N/A')
        
        # Add query-specific info
        info_html = f"<strong>{name}</strong><br>{city}<br>Enrollment: {enrollment}"
        
        if 'low_income_pct' in school:
            info_html += f"<br>Low-Income: {school['low_income_pct']}%"
        if 'graduation_rate' in school:
            info_html += f"<br>Graduation: {school['graduation_rate']}%"
        if 'student_teacher_ratio' in school:
            info_html += f"<br>Student-Teacher Ratio: {school['student_teacher_ratio']}"
        if 'ap_courses' in school and school['ap_courses']:
            info_html += f"<br>AP Courses: {school['ap_courses']}"
        
        markers_data.append({
            "position": {"lat": lat, "lng": lng},
            "title": name,
            "label": str(i),
            "info": info_html
        })
    
    map_config = {
        "center": {"lat": avg_lat, "lng": avg_lng},
        "markers": markers_data
    }
    
    map_config_json = html.escape(json.dumps(map_config))
    
    map_html = f'''
<div class="map-container" style="margin: 20px 0;">
    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 1.1rem;">📍 School Locations</h3>
        <div id="schoolMap" class="school-map" data-map-config="{map_config_json}" style="width: 100%; height: 400px; border-radius: 8px; overflow: hidden; background: #e5e7eb;"></div>
    </div>
</div>
'''
    
    return map_html


def _combine_response_components(
    summary: str, 
    chart_html: Optional[str], 
    map_html: Optional[str],
    data: List[Dict[str, Any]],
    query_type: str
) -> str:
    """Combine all components into a full HTML response."""
    
    components = []
    
    # Add summary
    components.append(f'<div class="executive-summary">{summary}</div>')
    
    # Add map (no charts)
    if map_html:
        components.append(map_html)
    
    # Add detailed data table
    components.append(_generate_data_table(data, query_type))
    
    return '\n'.join(components)


def _generate_data_table(data: List[Dict[str, Any]], query_type: str) -> str:
    """Generate a detailed data table."""
    
    if not data:
        return ""
    
    table_html = ['''
<div class="data-table-container" style="margin: 30px 0;">
    <h2 style="color: #1f2937; margin: 0 0 15px 0; font-size: 1.3rem;">📋 Detailed Data</h2>
    <div style="background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: linear-gradient(to right, #3b82f6, #6366f1); color: white;">
                <tr>
''']
    
    # Add table headers based on query type
    if query_type == "high_need_low_tech":
        table_html.append('<th style="padding: 12px; text-align: left;">School Name</th>')
        table_html.append('<th style="padding: 12px; text-align: left;">City</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Enrollment</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Low-Income %</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Per-Pupil $</th>')
        
    elif query_type == "high_grad_low_funding":
        table_html.append('<th style="padding: 12px; text-align: left;">School Name</th>')
        table_html.append('<th style="padding: 12px; text-align: left;">City</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Enrollment</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Graduation %</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Low-Income %</th>')
        
    elif query_type == "stem_excellence":
        table_html.append('<th style="padding: 12px; text-align: left;">School Name</th>')
        table_html.append('<th style="padding: 12px; text-align: left;">City</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Enrollment</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">AP Courses</th>')
        table_html.append('<th style="padding: 12px; text-align: right;">Student-Teacher</th>')
    
    table_html.append('</tr></thead><tbody>')
    
    # Add table rows
    for i, school in enumerate(data[:20], 1):  # Limit to 20 rows
        bg_color = '#f9fafb' if i % 2 == 0 else 'white'
        table_html.append(f'<tr style="background: {bg_color}; border-bottom: 1px solid #e5e7eb;">')
        
        if query_type == "high_need_low_tech":
            table_html.append(f'<td style="padding: 12px;">{school.get("school_name", "N/A")}</td>')
            table_html.append(f'<td style="padding: 12px;">{school.get("city_location", "N/A")}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{int(school.get("enrollment", 0))}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{school.get("low_income_pct", 0)}%</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">${int(school.get("per_pupil_total", 0)):,}</td>')
            
        elif query_type == "high_grad_low_funding":
            table_html.append(f'<td style="padding: 12px;">{school.get("school_name", "N/A")}</td>')
            table_html.append(f'<td style="padding: 12px;">{school.get("city_location", "N/A")}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{int(school.get("enrollment", 0))}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{school.get("graduation_rate", 0)}%</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{school.get("low_income_pct", 0)}%</td>')
            
        elif query_type == "stem_excellence":
            table_html.append(f'<td style="padding: 12px;">{school.get("school_name", "N/A")}</td>')
            table_html.append(f'<td style="padding: 12px;">{school.get("city_location", "N/A")}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{int(school.get("enrollment", 0))}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{school.get("ap_courses", 0) or 0}</td>')
            table_html.append(f'<td style="padding: 12px; text-align: right;">{school.get("student_teacher_ratio", 0)}</td>')
        
        table_html.append('</tr>')
    
    table_html.append('</tbody></table>')
    table_html.append('</div>')
    table_html.append('</div>')
    
    return '\n'.join(table_html)


def load_maps_api_key() -> Optional[str]:
    """Load Google Maps API key from environment variable or secrets file."""
    try:
        # First, try environment variable (for Cloud Run)
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if api_key and api_key.strip():
            return api_key.strip()
        
        # Fallback to secrets file (for local development)
        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secrets', 'maps_api_key.txt')
        if os.path.exists(key_path):
            with open(key_path, 'r') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Warning: Could not load Maps API key: {e}")
    return None

