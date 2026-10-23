---
id: risk-analytics
title: Risk Analytics and World Map
route: /analytics
roles: [viewer, analyst, reviewer, admin, executive]
status: implemented-foundation
---
# Why does the world map have no risk markers?
Country boundaries are available as a locally packaged basemap. Risk markers need verified country or location information linked to your workspace's cases. If that information is unavailable, the map explicitly labels its risk layer inactive. An unmarked country does not mean that it is safe or has zero fraud.

# How do I explore the map?
Select a country from the Region selector or click its outline. Use the zoom buttons to change scale and Reset to return to the world view. Focus the map and use arrow keys to pan, plus or minus to zoom, and Escape to reset. Hovering identifies a country without asserting that any case was observed there.

# What data do dashboard charts use?
The dashboard uses stored cases, investigation runs, upload processing states, and audit events from your current workspace. Choose a 7, 30, or 90 day period for activity history. Sample development workspaces are explicitly labeled. An unavailable metric is different from a successful response reporting zero.
