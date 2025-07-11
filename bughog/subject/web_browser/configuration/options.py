from dataclasses import dataclass, field


@dataclass(frozen=True)
class Default:
    pretty: str = field(default='Default', init=False)
    short: str = field(default='default', init=False)


@dataclass(frozen=True)
class BlockThirdPartyCookies:
    pretty: str = field(default='Block third-party cookies (beta)', init=False)
    short: str = field(default='btpc', init=False)


@dataclass(frozen=True)
class TrackingProtection:
    pretty: str = field(default='Tracking protection (beta)', init=False)
    short: str = field(default='tp', init=False)


@dataclass(frozen=True)
class PrivateBrowsing:
    pretty: str = field(default='Private browsing (beta)', init=False)
    short: str = field(default='pb', init=False)
