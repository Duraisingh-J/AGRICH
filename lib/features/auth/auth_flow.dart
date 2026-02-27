import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../core/i18n.dart';
import '../../core/models.dart';
import '../common/widgets.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key, required this.tagline});

  final String tagline;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const LeafLoader(size: 80),
                const SizedBox(height: 16),
                Text(
                  'AGRICHAIN',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                Text(tagline, style: Theme.of(context).textTheme.bodyLarge),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class AuthFlow extends StatefulWidget {
  const AuthFlow({
    super.key,
    required this.onAuthenticated,
    required this.i18n,
  });

  final ValueChanged<AppRole> onAuthenticated;
  final I18nController i18n;

  @override
  State<AuthFlow> createState() => _AuthFlowState();
}

class _AuthFlowState extends State<AuthFlow> {
  int _step = 0;
  AppRole? _selectedRole;
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _otpController = TextEditingController();
  int _kycStep = 1;

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 280),
              transitionBuilder: (child, animation) {
                return FadeTransition(
                  opacity: animation,
                  child: SlideTransition(
                    position: Tween<Offset>(
                      begin: const Offset(0, 0.04),
                      end: Offset.zero,
                    ).animate(animation),
                    child: child,
                  ),
                );
              },
              child: _buildByStep(context),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildByStep(BuildContext context) {
    switch (_step) {
      case 0:
        return _roleSelection(context);
      case 1:
        return _otpLogin(context);
      default:
        return _kycFlow(context);
    }
  }

  Widget _roleSelection(BuildContext context) {
    return Column(
      key: const ValueKey('role-selection'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Select your ecosystem',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 16),
        Expanded(
          child: GridView.count(
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            children: AppRole.values.map((role) {
              final isSelected = _selectedRole == role;
              return InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => setState(() => _selectedRole = role),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isSelected
                          ? Theme.of(context).colorScheme.primary
                          : Colors.transparent,
                      width: 1.8,
                    ),
                  ),
                  child: GlassCard(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 180),
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            color: isSelected
                                ? (Theme.of(context).brightness ==
                                          Brightness.dark
                                      ? AppPalette.darkSelected
                                      : AppPalette.lightSelected)
                                : Theme.of(context).brightness ==
                                      Brightness.dark
                                ? AppPalette.darkSurfaceAlt
                                : AppPalette.lightSurfaceAlt,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: isSelected
                                  ? Theme.of(context).colorScheme.primary
                                  : Theme.of(context).brightness ==
                                        Brightness.dark
                                  ? AppPalette.darkBorder
                                  : AppPalette.lightBorder,
                              width: 1.4,
                            ),
                          ),
                          child: Icon(
                            role.icon,
                            size: 28,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          role.title,
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(
                                fontWeight: isSelected
                                    ? FontWeight.w700
                                    : FontWeight.w600,
                              ),
                        ),
                        const SizedBox(height: 6),
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 180),
                          width: 26,
                          height: 4,
                          decoration: BoxDecoration(
                            color: isSelected
                                ? Theme.of(context).colorScheme.primary
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            onPressed: _selectedRole == null
                ? null
                : () => setState(() => _step = 1),
            child: const Text('Continue'),
          ),
        ),
      ],
    );
  }

  Widget _otpLogin(BuildContext context) {
    return Column(
      key: const ValueKey('otp-login'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('OTP Login', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                textInputAction: TextInputAction.next,
                autofillHints: const [AutofillHints.telephoneNumber],
                decoration: const InputDecoration(
                  labelText: 'Phone Number',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _otpController,
                maxLength: 6,
                keyboardType: TextInputType.number,
                textInputAction: TextInputAction.done,
                autofillHints: const [AutofillHints.oneTimeCode],
                onChanged: (value) {
                  setState(() {});
                  if (value.length == 6) {
                    FocusScope.of(context).unfocus();
                  }
                },
                decoration: const InputDecoration(
                  labelText: 'Enter OTP',
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Spacer(),
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            onPressed: _otpController.text.length == 6
                ? () => setState(() => _step = 2)
                : null,
            icon: const Icon(Icons.verified_user_rounded),
            label: const Text('Verify OTP'),
          ),
        ),
      ],
    );
  }

  Widget _kycFlow(BuildContext context) {
    final steps = ['Aadhaar upload', 'License upload', 'Land verification'];
    return Column(
      key: const ValueKey('kyc-flow'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'KYC Upload Flow',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 16),
        Text('Step $_kycStep/3'),
        const SizedBox(height: 8),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(steps[_kycStep - 1]),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () {
                  if (_kycStep < 3) {
                    setState(() => _kycStep++);
                  } else {
                    showDialog<void>(
                      context: context,
                      builder: (context) => AlertDialog(
                        icon: const Icon(
                          Icons.check_circle,
                          color: AppPalette.brandGreen,
                          size: 36,
                        ),
                        title: const Text('Verification Complete'),
                        content: const Text('KYC submitted successfully.'),
                        actions: [
                          TextButton(
                            onPressed: () {
                              Navigator.of(context).pop();
                              widget.onAuthenticated(_selectedRole!);
                            },
                            child: const Text('Enter AGRICHAIN'),
                          ),
                        ],
                      ),
                    );
                  }
                },
                icon: const Icon(Icons.upload_file_rounded),
                label: Text(_kycStep < 3 ? 'Upload & Continue' : 'Submit KYC'),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
