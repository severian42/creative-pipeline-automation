"""
Campaign orchestrator - main controller for campaign generation workflow.
"""

from typing import Dict, Callable, Optional
from .storage_manager import StorageManager
from .image_generator import ImageGenerator
from .creative_engine import CreativeEngine
from .compliance_agent import ComplianceAgent


class CampaignOrchestrator:
    """
    Main controller that orchestrates the entire campaign generation workflow.
    """
    
    def __init__(self, config):
        """
        Initialize orchestrator with all sub-components.
        
        Args:
            config: AppConfig instance
        """
        self.config = config
        
        # Initialize all components
        print("\n=== Initializing Campaign Orchestrator ===")
        self.storage_manager = StorageManager(config)
        self.image_generator = ImageGenerator(config)
        self.creative_engine = CreativeEngine()
        self.compliance_agent = ComplianceAgent(config)
        
        print("✓ All components initialized successfully\n")
    
    def _get_campaign_message(self, brief_data: dict, locale: Optional[str] = None, 
                             ab_variant: Optional[str] = None) -> str:
        """
        Get campaign message based on locale or A/B variant.
        
        Args:
            brief_data: Campaign brief data
            locale: Optional locale code (e.g., "en_US")
            ab_variant: Optional A/B variant name
        
        Returns:
            str: Campaign message
        """
        # Priority: A/B variant > Locale > Default
        
        # Check A/B testing variant
        if ab_variant:
            ab_config = brief_data.get("ab_testing", {})
            if ab_config.get("enabled"):
                variants = ab_config.get("variants", [])
                for variant in variants:
                    if variant.get("name") == ab_variant:
                        return variant.get("message", brief_data["campaign_message"])
        
        # Check locale-specific message
        if locale:
            locales = brief_data.get("locales", [])
            for locale_config in locales:
                locale_code = f"{locale_config.get('language')}_{locale_config.get('region')}"
                if locale_code == locale or locale_config.get("language") == locale.split("_")[0]:
                    return locale_config.get("message", brief_data["campaign_message"])
        
        # Default message
        return brief_data["campaign_message"]
    
    def get_available_locales(self, brief_data: dict) -> list:
        """
        Get list of available locales from brief.
        
        Args:
            brief_data: Campaign brief data
        
        Returns:
            list: List of locale codes
        """
        locales = brief_data.get("locales", [])
        return [f"{loc.get('language')}_{loc.get('region')}" for loc in locales]
    
    def get_available_ab_variants(self, brief_data: dict) -> list:
        """
        Get list of available A/B test variants from brief.
        
        Args:
            brief_data: Campaign brief data
        
        Returns:
            list: List of variant names
        """
        ab_config = brief_data.get("ab_testing", {})
        if not ab_config.get("enabled"):
            return []
        
        variants = ab_config.get("variants", [])
        return [v.get("name") for v in variants if v.get("name")]
    
    def execute_campaign(self, brief_data: dict, 
                        log_callback: Optional[Callable[[str], None]] = None,
                        locale: Optional[str] = None,
                        ab_variant: Optional[str] = None) -> dict:
        """
        Execute complete campaign generation workflow.
        
        Args:
            brief_data: Campaign brief dictionary from YAML
            log_callback: Optional callback function for real-time logging
            locale: Optional locale code (e.g., "en_US", "es_ES") for localized messages
            ab_variant: Optional A/B test variant name
        
        Returns:
            dict: Results dictionary with status, logs, and output paths
        """
        # Helper function for logging with progress updates
        def log(message: str):
            print(message)
            if log_callback:
                log_callback(message)
            # Small delay to ensure log is stored before next operation
            import time
            time.sleep(0.01)
        
        # Initialize results
        results = {
            "status": "processing",
            "campaign_id": brief_data.get("campaign_id", "unknown"),
            "locale": locale,
            "ab_variant": ab_variant,
            "logs": [],
            "output_paths": {},
            "errors": []
        }
        
        try:
            log("\n" + "="*60)
            log(f"Campaign: {brief_data.get('campaign_id', 'unknown')}")
            log("="*60)
            
            # Step 1: Validate campaign structure
            log("\n[Step 1/4] Validating campaign brief...")
            
            required_fields = ["campaign_id", "target_region", "target_audience", 
                             "campaign_message", "products"]
            for field in required_fields:
                if field not in brief_data:
                    error_msg = f"Missing required field: {field}"
                    log(f"  ✗ {error_msg}")
                    results["status"] = "failed"
                    results["errors"].append(error_msg)
                    return results
            
            products = brief_data.get("products", [])
            if len(products) < 2:
                error_msg = f"At least 2 products required, found {len(products)}"
                log(f"  ✗ {error_msg}")
                results["status"] = "failed"
                results["errors"].append(error_msg)
                return results
            
            log(f"  ✓ Campaign brief validated ({len(products)} products)")
            
            # Step 2: Compliance checks with auto-fix
            log("\n[Step 2/4] Running compliance checks with auto-fix...")
            results["progress"] = 20
            
            # Note: We need to get the message for the selected locale first for compliance checking
            # Get the campaign message based on locale/AB variant
            test_message = self._get_campaign_message(brief_data, locale, ab_variant)
            
            # Create a temporary brief data for compliance check with the selected message
            temp_brief_data = brief_data.copy()
            temp_brief_data["campaign_message"] = test_message
            
            is_compliant, compliance_reason, fixed_data = self.compliance_agent.validate_campaign(
                temp_brief_data, auto_fix=True, locale=locale, log_callback=log_callback
            )
            
            if not is_compliant:
                error_msg = f"Compliance check failed: {compliance_reason}"
                log(f"  ✗ {error_msg}")
                results["status"] = "failed"
                results["errors"].append(error_msg)
                return results
            
            # If message was fixed, use the fixed version and log the changes
            if fixed_data:
                log(f"  ✓ Compliance achieved with auto-fixes:")
                for fix in fixed_data.get("compliance_fixes", []):
                    log(f"    - Fix {fix['attempt']}: {fix['explanation']}")
                log(f"    - Final message: \"{fixed_data['campaign_message']}\"")
                
                # Update brief_data with fixed message
                brief_data = fixed_data
                results["compliance_fixes"] = fixed_data.get("compliance_fixes", [])
            else:
                log(f"  ✓ Compliance checks passed")
            
            # Step 3: Process each product
            log("\n[Step 3/4] Processing products and generating creatives...")
            results["progress"] = 50  # Update progress
            
            campaign_id = brief_data["campaign_id"]
            
            # Determine campaign message based on locale or A/B variant
            campaign_message = self._get_campaign_message(brief_data, locale, ab_variant)
            
            if locale:
                log(f"  Using locale: {locale} (AI models will generate content for this language)")
            if ab_variant:
                log(f"  Using A/B variant: {ab_variant}")
            log(f"  Campaign message: \"{campaign_message}\"")
            
            total_products = len(products)
            for idx, product in enumerate(products, 1):
                # Update progress
                product_progress = 50 + int((idx / total_products) * 40)
                results["progress"] = product_progress
                product_name = product.get("name", f"Product {idx}")
                product_description = product.get("description", "")
                asset_filename = product.get("asset_filename", product_name.lower().replace(" ", "_"))
                
                log(f"\n  Product {idx}/{len(products)}: {product_name}")
                log(f"  {'─' * 50}")
                
                # Try to find existing asset
                log(f"  Searching for existing asset: {asset_filename}")
                base_image = self.storage_manager.find_asset(asset_filename, log_callback)
                
                if base_image:
                    log(f"  ✓ Using existing asset")
                    asset_status = "reused"
                    
                    # Process all three aspect ratios with existing asset
                    aspect_ratios = ["1:1", "9:16", "16:9"]
                    product_outputs = {}
                    
                    for aspect_ratio in aspect_ratios:
                        try:
                            log(f"    Processing {aspect_ratio}...")
                            
                            # Process creative (resize + text overlay)
                            final_creative = self.creative_engine.process_creative(
                                base_image,
                                aspect_ratio,
                                campaign_message,
                                product_name
                            )
                            
                            # Upload/save creative
                            output_path = self.storage_manager.upload_creative(
                                campaign_id,
                                product_name,
                                aspect_ratio,
                                final_creative,
                                log_callback
                            )
                            
                            product_outputs[aspect_ratio] = output_path
                            log(f"    ✓ Saved {aspect_ratio} creative")
                            
                        except Exception as e:
                            error_msg = f"Error processing {aspect_ratio}: {str(e)}"
                            log(f"    ✗ {error_msg}")
                            results["errors"].append(error_msg)
                
                else:
                    log(f"  ✗ No existing asset found")
                    log(f"  Generating new images using Gemini...")
                    asset_status = "generated"
                    
                    try:
                        # Generate images for all aspect ratios
                        generated_images = self.image_generator.generate_all_aspect_ratios(
                            product_name,
                            product_description,
                            locale,
                            log_callback
                        )
                        
                        product_outputs = {}
                        
                        # Process each generated image
                        for aspect_ratio, generated_image in generated_images.items():
                            try:
                                log(f"    Processing {aspect_ratio}...")
                                
                                # Add text overlay
                                final_creative = self.creative_engine.add_text_overlay(
                                    generated_image,
                                    campaign_message,
                                    product_name
                                )
                                
                                # Upload/save creative
                                output_path = self.storage_manager.upload_creative(
                                    campaign_id,
                                    product_name,
                                    aspect_ratio,
                                    final_creative,
                                    log_callback
                                )
                                
                                product_outputs[aspect_ratio] = output_path
                                log(f"    ✓ Saved {aspect_ratio} creative")
                                
                            except Exception as e:
                                error_msg = f"Error processing {aspect_ratio}: {str(e)}"
                                log(f"    ✗ {error_msg}")
                                results["errors"].append(error_msg)
                    
                    except Exception as e:
                        error_msg = f"Error generating images: {str(e)}"
                        log(f"  ✗ {error_msg}")
                        results["errors"].append(error_msg)
                        continue
                
                # Store results for this product
                results["output_paths"][product_name] = {
                    "asset_status": asset_status,
                    "creatives": product_outputs
                }
                
                log(f"  ✓ Completed {product_name} ({len(product_outputs)} creatives)")
            
            # Step 4: Finalize
            log("\n[Step 4/4] Finalizing campaign...")
            results["progress"] = 95
            
            total_creatives = sum(
                len(p["creatives"]) 
                for p in results["output_paths"].values()
            )
            
            if total_creatives == 0:
                results["status"] = "failed"
                results["progress"] = 0
                error_msg = "No creatives were generated"
                log(f"  ✗ {error_msg}")
                results["errors"].append(error_msg)
            else:
                results["status"] = "completed"
                results["progress"] = 100
                log(f"  ✓ Campaign completed successfully!")
                log(f"  Generated {total_creatives} total creatives")
            
            log("\n" + "="*60)
            log("Campaign generation complete")
            log("="*60 + "\n")
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log(f"\n✗ {error_msg}")
            results["status"] = "failed"
            results["errors"].append(error_msg)
        
        return results

