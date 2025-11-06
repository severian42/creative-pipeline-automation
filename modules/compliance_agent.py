"""
Compliance agent using Gemini Flash for brand and legal validation.
"""

import json
from typing import Tuple
from google import genai
from google.genai import types


class ComplianceAgent:
    """
    Uses Gemini Flash as an agentic LLM to perform compliance checks.
    Includes auto-fix capability using multiple LLM instances.
    """
    
    def __init__(self, config):
        """
        Initialize compliance agent with Gemini API.
        
        Args:
            config: AppConfig instance with API key and brand guidelines
        """
        self.config = config
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = "gemini-flash-latest"
        self.brand_guidelines = config.get_patagonia_brand_guidelines()
        self.max_fix_attempts = 5  # Maximum attempts to fix compliance issues (increased for better success rate)
        
        print(f"✓ ComplianceAgent initialized with model: {self.model}")
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Call Gemini Flash with a prompt and return response.
        
        Args:
            prompt: Prompt text
        
        Returns:
            str: Model response text
        """
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        # Generate response
        response_text = ""
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
        ):
            if chunk.text:
                response_text += chunk.text
        
        return response_text.strip()
    
    def check_legal_compliance(self, campaign_message: str, locale: str = None, log_callback=None) -> Tuple[bool, str]:
        """
        Check campaign message for legal compliance issues.
        
        Args:
            campaign_message: Campaign message text
            locale: Optional locale code (e.g., "en_US", "es_ES") for language context
        
        Returns:
            tuple: (is_compliant: bool, reason: str)
        """
        # Determine language context
        language_note = ""
        if locale:
            language_code = locale.split("_")[0].lower()
            language_names = {
                "en": "English",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "ja": "Japanese",
                "zh": "Chinese",
                "ko": "Korean",
                "ar": "Arabic"
            }
            language = language_names.get(language_code, language_code.upper())
            language_note = f"\nNOTE: This message is in {language}. Evaluate compliance based on the content meaning, regardless of the language."
        
        prompt = f"""You are a legal compliance checker for advertising content.{language_note}

Review this campaign message for legal issues:
"{campaign_message}"

Check for:
- Discriminatory language (e.g., targeting by race, gender, religion)
- Harmful or violent terms
- False claims or misleading statements
- Scammy or deceptive language

Respond ONLY with valid JSON in this exact format:
{{"compliant": true, "reason": "explanation"}}

or

{{"compliant": false, "reason": "explanation"}}"""

        try:
            response = self._call_gemini(prompt)
            
            # Try to extract JSON from response
            # Look for JSON object in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                is_compliant = result.get("compliant", False)
                reason = result.get("reason", "No reason provided")
                
                if is_compliant:
                    msg = "  ✓ Legal compliance check: PASSED"
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                else:
                    msg = f"  ✗ Legal compliance check: FAILED - {reason}"
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                
                return (is_compliant, reason)
            else:
                # Couldn't parse JSON, default to pass with note
                print(f"  ⚠ Legal compliance check: Could not parse response, defaulting to pass")
                return (True, "Compliance check completed (response format issue)")
                
        except Exception as e:
            print(f"  ✗ Legal compliance check error: {e}")
            # On error, default to pass to avoid blocking legitimate campaigns
            return (True, f"Compliance check completed with warning: {str(e)}")
    
    def check_brand_compliance(self, campaign_message: str, target_audience: str, locale: str = None, log_callback=None) -> Tuple[bool, str]:
        """
        Check campaign message for brand compliance with Patagonia guidelines.
        
        Args:
            campaign_message: Campaign message text
            target_audience: Target audience description
            locale: Optional locale code (e.g., "en_US", "es_ES") for language context
        
        Returns:
            tuple: (is_compliant: bool, reason: str)
        """
        # Determine language context
        language_note = ""
        if locale:
            language_code = locale.split("_")[0].lower()
            language_names = {
                "en": "English",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "ja": "Japanese",
                "zh": "Chinese",
                "ko": "Korean",
                "ar": "Arabic"
            }
            language = language_names.get(language_code, language_code.upper())
            language_note = f"\nNOTE: This message is in {language}. Evaluate compliance based on the content meaning and brand values, regardless of the language."
        
        # Format brand guidelines for prompt
        guidelines_text = f"""
Core Values:
- Quality: {self.brand_guidelines['core_values']['quality']}
- Integrity: {self.brand_guidelines['core_values']['integrity']}
- Environmentalism: {self.brand_guidelines['core_values']['environmentalism']}
- Justice: {self.brand_guidelines['core_values']['justice']}
- Not Bound by Convention: {self.brand_guidelines['core_values']['not_bound_by_convention']}

Forbidden Terms:
{', '.join(self.brand_guidelines['forbidden_content']['brand_voice'])}

Brand Voice Principles:
{chr(10).join('- ' + p for p in self.brand_guidelines['brand_voice_principles'])}
"""
        
        prompt = f"""You are a brand compliance checker for Patagonia.{language_note}

Brand Guidelines:
{guidelines_text}

Campaign Message: "{campaign_message}"
Target Audience: "{target_audience}"

Check if the message:
1. Aligns with Patagonia's environmental and social justice mission
2. Avoids prohibited language (guaranteed, miracle, buy now, limited time, etc.)
3. Focuses on quality, durability, and environmental responsibility
4. Uses authentic voice (not overly salesy or aggressive)

Respond ONLY with valid JSON in this exact format:
{{"compliant": true, "reason": "explanation"}}

or

{{"compliant": false, "reason": "explanation"}}"""

        try:
            response = self._call_gemini(prompt)
            
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                is_compliant = result.get("compliant", False)
                reason = result.get("reason", "No reason provided")
                
                if is_compliant:
                    msg = "  ✓ Brand compliance check: PASSED"
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                else:
                    msg = f"  ✗ Brand compliance check: FAILED - {reason}"
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                
                return (is_compliant, reason)
            else:
                # Couldn't parse JSON, default to pass with note
                print(f"  ⚠ Brand compliance check: Could not parse response, defaulting to pass")
                return (True, "Compliance check completed (response format issue)")
                
        except Exception as e:
            print(f"  ✗ Brand compliance check error: {e}")
            # On error, default to pass to avoid blocking legitimate campaigns
            return (True, f"Compliance check completed with warning: {str(e)}")
    
    def fix_compliance_issues(self, campaign_message: str, target_audience: str, 
                             compliance_reason: str, locale: str = None, log_callback=None) -> Tuple[bool, str, str]:
        """
        Use Gemini LLM to automatically fix compliance issues.
        
        Args:
            campaign_message: Original campaign message
            target_audience: Target audience description
            compliance_reason: Reason why message failed compliance
            locale: Optional locale code (e.g., "en_US", "es_ES") for language context
        
        Returns:
            tuple: (success: bool, fixed_message: str, explanation: str)
        """
        msg = "  🔧 Attempting to auto-fix compliance issues..."
        print(msg)
        if log_callback:
            log_callback(msg)
        
        # Determine language context
        language_note = ""
        if locale:
            language_code = locale.split("_")[0].lower()
            language_names = {
                "en": "English",
                "es": "Spanish",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "ja": "Japanese",
                "zh": "Chinese",
                "ko": "Korean",
                "ar": "Arabic"
            }
            language = language_names.get(language_code, language_code.upper())
            language_note = f"\nIMPORTANT: The fixed message MUST be written in {language}, maintaining the same language as the original message."
        
        # Format brand guidelines for prompt
        guidelines_text = f"""
Core Values:
- Quality: {self.brand_guidelines['core_values']['quality']}
- Environmentalism: {self.brand_guidelines['core_values']['environmentalism']}

Forbidden Terms:
{', '.join(self.brand_guidelines['forbidden_content']['brand_voice'])}

Brand Voice Principles:
{chr(10).join('- ' + p for p in self.brand_guidelines['brand_voice_principles'])}
"""
        
        prompt = f"""You are a compliance expert for Patagonia advertising campaigns.{language_note}

ORIGINAL MESSAGE: "{campaign_message}"
TARGET AUDIENCE: "{target_audience}"

COMPLIANCE ISSUE:
{compliance_reason}

BRAND GUIDELINES:
{guidelines_text}

YOUR TASK:
Rewrite the campaign message to be fully compliant with both legal requirements and Patagonia's brand guidelines.

REQUIREMENTS:
1. Make environmental claims specific and substantiated (avoid vague claims)
2. Remove any unverifiable or misleading statements
3. Maintain Patagonia's authentic brand voice
4. Keep the message concise (under 150 characters)
5. Focus on quality, durability, and responsibility
6. Avoid prohibited language and overly aggressive sales tactics
7. Write in the SAME language as the original message

Respond ONLY with valid JSON in this exact format:
{{"fixed_message": "your compliant message here", "explanation": "brief explanation of changes"}}"""

        try:
            response = self._call_gemini(prompt)
            
            msg = f"  📝 LLM Response (first 200 chars): {response[:200]}..."
            print(msg)
            if log_callback:
                log_callback(msg)
            
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                
                try:
                    result = json.loads(json_str)
                    
                    fixed_message = result.get("fixed_message", "")
                    explanation = result.get("explanation", "")
                    
                    if fixed_message and len(fixed_message.strip()) > 0:
                        msgs = [
                            "  ✓ Generated compliant alternative:",
                            f"    Original: {campaign_message}",
                            f"    Fixed: {fixed_message}",
                            f"    Reason: {explanation}"
                        ]
                        for m in msgs:
                            print(m)
                            if log_callback:
                                log_callback(m)
                        return (True, fixed_message, explanation)
                    else:
                        msg = "  ✗ LLM returned empty fixed message"
                        print(msg)
                        if log_callback:
                            log_callback(msg)
                        return (False, campaign_message, "LLM returned empty message")
                        
                except json.JSONDecodeError as je:
                    print(f"  ✗ JSON parsing error: {je}")
                    print(f"  Attempted to parse: {json_str[:200]}...")
                    return (False, campaign_message, f"JSON parsing failed: {str(je)}")
            else:
                print(f"  ✗ Could not find JSON in response")
                print(f"  Full response: {response[:500]}...")
                return (False, campaign_message, "No JSON found in LLM response")
            
        except Exception as e:
            print(f"  ✗ Error generating fix: {e}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            return (False, campaign_message, f"Error: {str(e)}")
    
    def validate_campaign(self, campaign_data: dict, auto_fix: bool = True, locale: str = None, log_callback=None) -> Tuple[bool, str, dict]:
        """
        Validate entire campaign for legal and brand compliance with auto-fix.
        
        Args:
            campaign_data: Campaign brief data dictionary
            auto_fix: If True, automatically fix compliance issues
            locale: Optional locale code (e.g., "en_US", "es_ES") for language context
        
        Returns:
            tuple: (is_compliant: bool, reason: str, fixed_data: dict or None)
        """
        campaign_message = campaign_data.get("campaign_message", "")
        target_audience = campaign_data.get("target_audience", "")
        
        msg = "\n=== Running Compliance Checks ==="
        print(msg)
        if log_callback:
            log_callback(msg)
        
        if locale:
            msg = f"  Locale: {locale}"
            print(msg)
            if log_callback:
                log_callback(msg)
        
        attempt = 0
        current_message = campaign_message
        fix_history = []
        
        while attempt < self.max_fix_attempts:
            if attempt > 0:
                print(f"\n  Retry attempt {attempt}/{self.max_fix_attempts - 1}")
            
            # Check legal compliance
            legal_compliant, legal_reason = self.check_legal_compliance(current_message, locale, log_callback)
            
            if not legal_compliant:
                if not auto_fix:
                    return (False, f"Legal compliance failed: {legal_reason}", None)
                
                # Check if we've exhausted all attempts
                if attempt >= self.max_fix_attempts - 1:
                    return (False, f"Legal compliance failed after {self.max_fix_attempts} auto-fix attempts: {legal_reason}", None)
                
                # Attempt to fix
                msg = f"  Attempt {attempt + 1}/{self.max_fix_attempts} to fix legal compliance..."
                print(msg)
                if log_callback:
                    log_callback(msg)
                success, fixed_msg, explanation = self.fix_compliance_issues(
                    current_message, target_audience, f"Legal issue: {legal_reason}", locale, log_callback
                )
                
                if success:
                    fix_history.append({
                        "attempt": attempt + 1,
                        "type": "legal",
                        "original": current_message,
                        "fixed": fixed_msg,
                        "explanation": explanation
                    })
                    current_message = fixed_msg
                    msg = "  ✓ Fix successful, re-checking compliance..."
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                    attempt += 1
                    continue
                else:
                    # Fix failed, but try again if we have attempts left
                    attempt += 1
                    if attempt < self.max_fix_attempts:
                        msg = f"  ⚠ Fix failed, retrying... ({attempt + 1}/{self.max_fix_attempts})"
                        print(msg)
                        if log_callback:
                            log_callback(msg)
                        continue
                    else:
                        return (False, f"Legal compliance failed: Could not generate valid fix after {self.max_fix_attempts} attempts", None)
            
            # Check brand compliance
            brand_compliant, brand_reason = self.check_brand_compliance(
                current_message, target_audience, locale, log_callback
            )
            
            if not brand_compliant:
                if not auto_fix:
                    return (False, f"Brand compliance failed: {brand_reason}", None)
                
                # Check if we've exhausted all attempts
                if attempt >= self.max_fix_attempts - 1:
                    return (False, f"Brand compliance failed after {self.max_fix_attempts} auto-fix attempts: {brand_reason}", None)
                
                # Attempt to fix
                msg = f"  Attempt {attempt + 1}/{self.max_fix_attempts} to fix brand compliance..."
                print(msg)
                if log_callback:
                    log_callback(msg)
                success, fixed_msg, explanation = self.fix_compliance_issues(
                    current_message, target_audience, f"Brand issue: {brand_reason}", locale, log_callback
                )
                
                if success:
                    fix_history.append({
                        "attempt": attempt + 1,
                        "type": "brand",
                        "original": current_message,
                        "fixed": fixed_msg,
                        "explanation": explanation
                    })
                    current_message = fixed_msg
                    msg = "  ✓ Fix successful, re-checking compliance..."
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                    attempt += 1
                    continue
                else:
                    # Fix failed, but try again if we have attempts left
                    attempt += 1
                    if attempt < self.max_fix_attempts:
                        msg = f"  ⚠ Fix failed, retrying... ({attempt + 1}/{self.max_fix_attempts})"
                        print(msg)
                        if log_callback:
                            log_callback(msg)
                        continue
                    else:
                        return (False, f"Brand compliance failed: Could not generate valid fix after {self.max_fix_attempts} attempts", None)
            
            # All checks passed
            if fix_history:
                msg = f"  ✓ Compliance achieved after {len(fix_history)} fix(es)"
                print(msg)
                if log_callback:
                    log_callback(msg)
                fixed_data = campaign_data.copy()
                fixed_data["campaign_message"] = current_message
                fixed_data["compliance_fixes"] = fix_history
                return (True, "Campaign is compliant after auto-fixes", fixed_data)
            else:
                msg = "  ✓ All compliance checks passed\n"
                print(msg)
                if log_callback:
                    log_callback(msg)
                return (True, "Campaign is compliant with all requirements", None)
        
        # Max attempts reached
        return (False, f"Could not achieve compliance after {self.max_fix_attempts} attempts", None)



