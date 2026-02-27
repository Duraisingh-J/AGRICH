import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../common/widgets.dart';

class ProductJourneyScreen extends StatelessWidget {
  const ProductJourneyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Product Journey')),
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Hero(
                tag: 'product-hero',
                child: GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 60,
                            height: 60,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(12),
                              color: AppPalette.brandGreen.withValues(
                                alpha: 0.24,
                              ),
                            ),
                            child: const Icon(Icons.image_rounded),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Organic Tomato Batch'),
                                Text(
                                  'Farm: Green Valley',
                                  style: TextStyle(
                                    color:
                                        Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? const Color(0xFFB9C7C0)
                                        : const Color(0xFF475467),
                                  ),
                                ),
                                Text(
                                  'Harvest: 24 Feb 2026',
                                  style: TextStyle(
                                    color:
                                        Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? const Color(0xFFB9C7C0)
                                        : const Color(0xFF475467),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Chip(
                            label: const Text('Organic'),
                            backgroundColor: AppPalette.brandGreen.withValues(
                              alpha: 0.24,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const _TimelineItem(
                title: 'Farmer',
                subtitle: 'Karthik Farms · 08:10 AM',
              ),
              const _TimelineItem(
                title: 'Distributor',
                subtitle: 'SouthCold Logistics · 11:42 AM',
              ),
              const _TimelineItem(
                title: 'Retailer',
                subtitle: 'FreshMart, Bengaluru · 03:10 PM',
              ),
              const SizedBox(height: 12),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Location Map Snippet',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 10),
                    Container(
                      height: 120,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        color: Theme.of(context).brightness == Brightness.dark
                            ? AppPalette.darkSelected
                            : AppPalette.lightSelected,
                      ),
                      alignment: Alignment.center,
                      child: const Icon(Icons.location_on_rounded, size: 34),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AI Smart Insights',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 10),
                    const _MetricRow('Freshness Score', '91'),
                    const _MetricRow('Carbon Footprint', 'Low'),
                    const _MetricRow('Allergy Safe?', 'Yes'),
                    const _MetricRow('Trust Score', '82'),
                    const SizedBox(height: 10),
                    FilledButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.picture_as_pdf_rounded),
                      label: const Text('Download Certificate (PDF)'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TimelineItem extends StatelessWidget {
  const _TimelineItem({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: const BoxDecoration(
                  color: AppPalette.brandGreen,
                  shape: BoxShape.circle,
                ),
              ),
              Container(
                width: 2,
                height: 36,
                color: Theme.of(context).brightness == Brightness.dark
                    ? AppPalette.premiumGold
                    : AppPalette.brandGreen,
              ),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: GlassCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [Text(title), Text(subtitle)],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  const _MetricRow(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(
              fontFamily: 'Space Grotesk',
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
