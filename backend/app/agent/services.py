from dataclasses import dataclass

from app.services.advice import Explainer, VerdictDecider
from app.services.alternatives import AlternativeChecker
from app.services.ecosystem_detection import EcosystemResolver
from app.services.package_input import DependencyInputParser
from app.services.scoring import HealthScorer
from app.services.signals import SignalSource


@dataclass(frozen=True)
class AgentServices:
    input_parser: DependencyInputParser
    detector: EcosystemResolver
    collector: SignalSource
    scorer: HealthScorer
    decider: VerdictDecider
    explainer: Explainer
    alternatives: AlternativeChecker
