# SPDX-License-Identifier: GPL-3.0-or-later
"""Sector plugins. Automotive is implemented in ti_framework.layer1/layer2.automotive.

Shipping and power are interface stubs only (Whitepaper §6, Methodological Challenges 5–6).
They subclass the same Layer-1 ``Benchmark`` / Layer-2 ``ProductEmissions`` contracts so they
slot into the unchanged Layer-3 core when implemented.
"""
