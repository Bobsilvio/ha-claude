"""Response quality metrics and scoring system.

Inspired by nanobot: Practical quality metrics to evaluate:
- Response completeness
- Answer relevance
- Confidence scoring
- Error rates
- User satisfaction prediction
"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseQuality(Enum):
    """Response quality levels."""
    EXCELLENT = "excellent"  # 0.85-1.0
    GOOD = "good"            # 0.70-0.85
    FAIR = "fair"            # 0.50-0.70
    POOR = "poor"            # < 0.50


@dataclass
class QualityMetric:
    """Individual quality metric."""
    name: str
    score: float  # 0.0 to 1.0
    weight: float  # Importance weight
    reason: str = ""
    
    def weighted_score(self) -> float:
        """Get weighted score."""
        return self.score * self.weight


class ResponseQualityAnalyzer:
    """Analyzes response quality using multiple metrics."""
    
    # Patterns indicating issues
    CONFIDENCE_PATTERNS = [
        (r"i'm\s+(not\s+)?sure", 0.5),
        (r"i\s+(don't\s+)?know", 0.3),
        (r"uncertain", 0.4),
        (r"might\s+(be|not)", 0.6),
        (r"possibly|probably", 0.7),
        (r"definitely|certainly", 0.95),
        (r"i'm confident", 0.9),
    ]
    
    # Patterns indicating completeness
    COMPLETENESS_PATTERNS = [
        (r"step\s+\d+", 0.8),
        (r"to\s+summarize|in\s+summary", 0.9),
        (r"also|additionally|furthermore", 0.7),
        (r"however|but|alternatively", 0.8),
    ]
    
    # Error indicators
    ERROR_PATTERNS = [
        r"error|failed|exception|invalid",
        r"not\s+found|doesn't\s+exist",
        r"permission\s+denied|unauthorized",
        r"timeout|timed\s+out",
    ]
    
    def __init__(self):
        """Initialize analyzer."""
        self.metrics_history: List[Dict[str, Any]] = []
    
    def _calculate_length_score(self, text: str) -> float:
        """Score based on response length.
        
        Too short (<50 words) or too long (>2000 words) reduces quality.
        """
        word_count = len(text.split())
        
        if word_count < 10:
            return 0.1
        elif word_count < 50:
            return 0.5
        elif word_count < 2000:
            return 1.0
        elif word_count < 5000:
            return 0.8
        else:
            return 0.3  # Way too long
    
    def _calculate_structure_score(self, text: str) -> float:
        """Score based on response structure.
        
        Looks for indicators of well-structured response.
        """
        score = 0.5
        
        # Count paragraphs (good indicator of structure)
        paragraphs = len([p for p in text.split('\n\n') if p.strip()])
        if paragraphs >= 2:
            score += 0.2
        if paragraphs >= 4:
            score += 0.15
        
        # Lists/formatting
        if re.search(r'^[\s]*[-•*]\s+', text, re.MULTILINE):
            score += 0.15
        
        # Headings
        if re.search(r'^#+\s+', text, re.MULTILINE):
            score += 0.1
        
        # Code blocks
        if '```' in text:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_confidence_score(self, text: str) -> float:
        """Score based on confidence language."""
        text_lower = text.lower()
        total_score = 0.7  # Default neutral
        pattern_matches = 0
        
        for pattern, pattern_score in self.CONFIDENCE_PATTERNS:
            if re.search(pattern, text_lower):
                total_score = max(total_score, pattern_score)
                pattern_matches += 1
        
        # Normalize
        return min(total_score, 1.0)
    
    def _calculate_completeness_score(self, text: str) -> float:
        """Score based on completeness indicators."""
        text_lower = text.lower()
        score = 0.5
        matches = 0
        
        for pattern, pattern_score in self.COMPLETENESS_PATTERNS:
            if re.search(pattern, text_lower):
                matches += 1
        
        # Score based on completeness indicators
        score = 0.5 + (matches * 0.15)
        
        # Check for conclusion
        if re.search(r'(conclusion|in\s+conclusion|to\s+conclude|finally)', text_lower):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_error_rate(self, text: str) -> float:
        """Calculate error indicators.
        
        Returns: Score (0.0 = many errors, 1.0 = no errors)
        """
        error_count = 0
        
        for pattern in self.ERROR_PATTERNS:
            error_count += len(re.findall(pattern, text.lower()))
        
        # Normalize error count to 0-1 range
        error_score = 1.0 - min(error_count * 0.05, 1.0)
        
        return max(error_score, 0.0)
    
    def _calculate_tool_usage_score(self, tool_count: int, errors: int) -> float:
        """Score based on tool usage efficiency.
        
        Args:
            tool_count: Number of tools used
            errors: Number of tool errors
        """
        if tool_count == 0:
            return 0.8  # No tools needed (fine for some queries)
        
        # Error rate in tools
        error_rate = errors / tool_count if tool_count > 0 else 0
        
        if error_rate == 0:
            return 1.0
        elif error_rate < 0.1:
            return 0.9
        elif error_rate < 0.3:
            return 0.7
        else:
            return 0.3
    
    def analyze(self,
                text: str,
                tool_count: int = 0,
                tool_errors: int = 0,
                thinking_used: bool = False,
                provider: str = "") -> Dict[str, Any]:
        """Analyze response quality.
        
        Args:
            text: Response text
            tool_count: Number of tools used
            tool_errors: Number of tool failures
            thinking_used: Whether extended thinking was used
            provider: AI provider used
            
        Returns:
            Quality analysis dict
        """
        metrics: List[QualityMetric] = [
            QualityMetric("length", self._calculate_length_score(text), 0.15,
                         "Response length appropriateness"),
            QualityMetric("structure", self._calculate_structure_score(text), 0.20,
                         "Response structure and formatting"),
            QualityMetric("confidence", self._calculate_confidence_score(text), 0.20,
                         "Confidence in answer"),
            QualityMetric("completeness", self._calculate_completeness_score(text), 0.25,
                         "Response completeness"),
            QualityMetric("errors", self._calculate_error_rate(text), 0.10,
                         "Error indicators in response"),
            QualityMetric("tool_usage", self._calculate_tool_usage_score(tool_count, tool_errors), 0.10,
                         "Tool usage efficiency"),
        ]
        
        # Calculate overall score
        total_weight = sum(m.weight for m in metrics)
        weighted_sum = sum(m.weighted_score() for m in metrics)
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Determine quality level
        if overall_score >= 0.85:
            quality_level = ResponseQuality.EXCELLENT
        elif overall_score >= 0.70:
            quality_level = ResponseQuality.GOOD
        elif overall_score >= 0.50:
            quality_level = ResponseQuality.FAIR
        else:
            quality_level = ResponseQuality.POOR
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(overall_score, 3),
            "quality_level": quality_level.value,
            "metrics": {m.name: {"score": round(m.score, 3), "weight": m.weight, "reason": m.reason} 
                       for m in metrics},
            "tool_statistics": {
                "tools_used": tool_count,
                "tool_errors": tool_errors,
                "error_rate": f"{tool_errors / max(tool_count, 1) * 100:.1f}%",
            },
            "features_used": {
                "extended_thinking": thinking_used,
                "provider": provider,
            },
            "recommendations": self._get_recommendations(overall_score, metrics),
        }
        
        self.metrics_history.append(analysis)
        
        return analysis
    
    def _get_recommendations(self, score: float, metrics: List[QualityMetric]) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        # Find lowest scoring metrics
        lowest_metrics = sorted(metrics, key=lambda m: m.score)[:2]
        
        for metric in lowest_metrics:
            if metric.name == "length" and metric.score < 0.7:
                recommendations.append("Consider providing a more detailed response")
            elif metric.name == "structure" and metric.score < 0.7:
                recommendations.append("Improve response structure with headings or lists")
            elif metric.name == "completeness" and metric.score < 0.7:
                recommendations.append("Provide more complete information with summary")
            elif metric.name == "confidence" and metric.score < 0.6:
                recommendations.append("Increase confidence level or clarify uncertainties")
            elif metric.name == "errors" and metric.score < 0.7:
                recommendations.append("Review response for errors and fix issues")
        
        if score < 0.6:
            recommendations.append("Consider using extended thinking for complex queries")
        
        return recommendations if recommendations else ["Response quality is good"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get quality metrics statistics."""
        if not self.metrics_history:
            return {"responses_analyzed": 0}
        
        scores = [m["overall_score"] for m in self.metrics_history]
        levels = [m["quality_level"] for m in self.metrics_history]
        
        return {
            "responses_analyzed": len(self.metrics_history),
            "average_score": round(sum(scores) / len(scores), 3),
            "min_score": min(scores),
            "max_score": max(scores),
            "quality_distribution": {
                "excellent": levels.count("excellent"),
                "good": levels.count("good"),
                "fair": levels.count("fair"),
                "poor": levels.count("poor"),
            },
        }


# Global analyzer instance
_quality_analyzer: Optional[ResponseQualityAnalyzer] = None


def get_quality_analyzer() -> ResponseQualityAnalyzer:
    """Get or create global quality analyzer."""
    global _quality_analyzer
    if _quality_analyzer is None:
        _quality_analyzer = ResponseQualityAnalyzer()
    return _quality_analyzer
