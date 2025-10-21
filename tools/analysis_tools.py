"""
ADK-Compatible Analysis Tool Functions
Statistical analysis and data processing tools
"""
from typing import Dict, Any, List
from google.adk.tools import ToolContext
import pandas as pd
import numpy as np


def calculate_statistics(
    data: List[Dict[str, Any]],
    column: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Calculate statistical summary for a numeric column in the data.
    
    Use this tool to get mean, median, std dev, min, max, and percentiles
    for any numeric field in your dataset.
    
    Args:
        data: List of dictionaries containing the data
        column: Name of the numeric column to analyze
        
    Returns:
        Dictionary with statistical measures including mean, median, std, min, max, percentiles
    """
    try:
        if not data:
            return {
                "status": "error",
                "message": "No data provided"
            }
        
        df = pd.DataFrame(data)
        
        if column not in df.columns:
            return {
                "status": "error",
                "message": f"Column '{column}' not found in data"
            }
        
        col_data = pd.to_numeric(df[column], errors='coerce').dropna()
        
        if len(col_data) == 0:
            return {
                "status": "error",
                "message": f"No numeric data in column '{column}'"
            }
        
        stats = {
            "status": "success",
            "column": column,
            "count": int(len(col_data)),
            "mean": float(col_data.mean()),
            "median": float(col_data.median()),
            "std": float(col_data.std()),
            "min": float(col_data.min()),
            "max": float(col_data.max()),
            "percentile_25": float(col_data.quantile(0.25)),
            "percentile_75": float(col_data.quantile(0.75))
        }
        
        # Store in context
        tool_context.state[f"last_stats_{column}"] = stats
        
        return stats
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error calculating statistics: {str(e)}"
        }


def identify_trends(
    data: List[Dict[str, Any]],
    metric_column: str,
    group_by_column: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Identify trends by grouping data and calculating metrics.
    
    Use this tool to see how metrics vary across different groups
    (e.g., average scores by district, enrollment by state).
    
    Args:
        data: List of dictionaries containing the data
        metric_column: Numeric column to aggregate
        group_by_column: Column to group by
        
    Returns:
        Dictionary with grouped statistics and trend insights
    """
    try:
        if not data:
            return {
                "status": "error",
                "message": "No data provided"
            }
        
        df = pd.DataFrame(data)
        
        if metric_column not in df.columns or group_by_column not in df.columns:
            return {
                "status": "error",
                "message": f"Required columns not found"
            }
        
        df[metric_column] = pd.to_numeric(df[metric_column], errors='coerce')
        
        grouped = df.groupby(group_by_column)[metric_column].agg([
            'mean', 'median', 'count', 'std'
        ]).round(2)
        
        results = grouped.to_dict('index')
        
        # Identify top and bottom performers
        sorted_groups = grouped.sort_values('mean', ascending=False)
        
        analysis = {
            "status": "success",
            "metric": metric_column,
            "grouped_by": group_by_column,
            "group_count": len(results),
            "groups": {str(k): {
                "mean": float(v['mean']) if not pd.isna(v['mean']) else None,
                "median": float(v['median']) if not pd.isna(v['median']) else None,
                "count": int(v['count']),
                "std": float(v['std']) if not pd.isna(v['std']) else None
            } for k, v in results.items()},
            "top_3": [str(x) for x in sorted_groups.head(3).index.tolist()],
            "bottom_3": [str(x) for x in sorted_groups.tail(3).index.tolist()]
        }
        
        tool_context.state["last_trend_analysis"] = analysis
        
        return analysis
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error identifying trends: {str(e)}"
        }


def compare_groups(
    data: List[Dict[str, Any]],
    group_column: str,
    metric_columns: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Compare multiple metrics across different groups.
    
    Use this tool to do side-by-side comparisons of groups on multiple metrics.
    
    Args:
        data: List of dictionaries containing the data
        group_column: Column defining the groups to compare
        metric_columns: List of numeric columns to compare
        
    Returns:
        Dictionary with comparison results for each metric across groups
    """
    try:
        if not data:
            return {
                "status": "error",
                "message": "No data provided"
            }
        
        df = pd.DataFrame(data)
        
        if group_column not in df.columns:
            return {
                "status": "error",
                "message": f"Group column '{group_column}' not found"
            }
        
        comparisons = {}
        
        for metric in metric_columns:
            if metric not in df.columns:
                continue
                
            df[metric] = pd.to_numeric(df[metric], errors='coerce')
            grouped = df.groupby(group_column)[metric].mean().round(2)
            
            comparisons[metric] = {
                str(k): float(v) if not pd.isna(v) else None 
                for k, v in grouped.to_dict().items()
            }
        
        result = {
            "status": "success",
            "grouped_by": group_column,
            "metrics_compared": len(comparisons),
            "comparisons": comparisons
        }
        
        tool_context.state["last_comparison"] = result
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error comparing groups: {str(e)}"
        }


def identify_outliers(
    data: List[Dict[str, Any]],
    column: str,
    threshold_std: float = 2.0,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Identify outliers in a numeric column using standard deviation method.
    
    Use this tool to find schools or districts with unusually high or low values.
    
    Args:
        data: List of dictionaries containing the data
        column: Numeric column to analyze for outliers
        threshold_std: Number of standard deviations to consider as outlier (default: 2.0)
        
    Returns:
        Dictionary with outlier information and flagged records
    """
    try:
        if not data:
            return {
                "status": "error",
                "message": "No data provided"
            }
        
        df = pd.DataFrame(data)
        
        if column not in df.columns:
            return {
                "status": "error",
                "message": f"Column '{column}' not found"
            }
        
        df[column] = pd.to_numeric(df[column], errors='coerce')
        df_clean = df.dropna(subset=[column])
        
        mean = df_clean[column].mean()
        std = df_clean[column].std()
        
        lower_bound = mean - (threshold_std * std)
        upper_bound = mean + (threshold_std * std)
        
        outliers = df_clean[
            (df_clean[column] < lower_bound) | 
            (df_clean[column] > upper_bound)
        ]
        
        result = {
            "status": "success",
            "column": column,
            "mean": float(mean),
            "std": float(std),
            "threshold_std": threshold_std,
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "outlier_count": len(outliers),
            "total_count": len(df_clean),
            "outlier_percentage": round((len(outliers) / len(df_clean)) * 100, 2) if len(df_clean) > 0 else 0,
            "outliers": outliers.to_dict('records')[:20]  # Limit to first 20
        }
        
        if tool_context:
            tool_context.state[f"outliers_{column}"] = result
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error identifying outliers: {str(e)}"
        }

