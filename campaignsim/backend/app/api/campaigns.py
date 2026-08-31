"""A/B campaign & variant API routes — launch, poll, score, recommend.

Split from the former monolithic simulation.py (Phase 0 restructure). Behavior
is unchanged; routes still live under /api/simulation via the shared
simulation_bp blueprint."""

import json
import os
import traceback
from dataclasses import asdict
from flask import request, jsonify, g

from . import simulation_bp
from ..config import Config
from ..extensions import db
from ..models.orm import SimulationRecord, CampaignRecord, CampaignVariantRecord
from ..services.simulation_runner import SimulationRunner
from ..services.simulation_helpers import _campaigns_dir, _save_campaign, _load_campaign
from ..utils.logger import get_logger
from ..utils.locale import t

logger = get_logger('campaignsim.api.campaigns')

# ============== Phase 2 — Channel Variant Simulation ==============

@simulation_bp.route('/launch_variant', methods=['POST'])
def launch_variant():
    """Launch a single channel variant simulation.

    Creates a variant-specific simulation directory, writes the config,
    copies the persona profiles CSV, and starts the channel simulation
    subprocess via SimulationRunner.

    Request body:
    {
        "simulation_id": "...",       // parent simulation ID (used to locate profiles)
        "variant_id": "variant_0",    // unique ID for this variant run
        "channel": "instagram",       // instagram | email | tiktok | linkedin
        "campaign_content": "...",    // full campaign text with channel framing
        "num_rounds": 10              // simulation rounds (default 10)
    }

    Response:
    {
        "success": true,
        "data": {
            "variant_sim_id": "...",
            "simulation_dir": "..."
        }
    }
    """
    import shutil

    try:
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id")
        if not simulation_id:
            return jsonify({"success": False, "error": t("api.requireSimulationId")}), 400

        variant_id = data.get("variant_id", "variant_0")
        channel = data.get("channel", "instagram")
        campaign_content = data.get("campaign_content", "")

        if not campaign_content:
            return jsonify({"success": False, "error": "campaign_content is required"}), 400

        from ..services.channel_registry import get_channel
        channel_def = get_channel(g.current_user.id, channel)
        if channel_def is None:
            return jsonify({"success": False, "error": f"Unknown channel '{channel}'"}), 400

        num_rounds = int(data.get("num_rounds") or channel_def.mechanics.get("max_rounds_default", 10))

        # Locate parent simulation dir (contains twitter_profiles.csv)
        parent_sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, simulation_id)
        profiles_src = os.path.join(parent_sim_dir, "twitter_profiles.csv")
        if not os.path.exists(profiles_src):
            return jsonify({
                "success": False,
                "error": (
                    f"twitter_profiles.csv not found in simulation {simulation_id}. "
                    "Run /prepare first to generate persona profiles."
                )
            }), 400

        # Create variant simulation directory
        variant_sim_id = f"{simulation_id}__{variant_id}"
        variant_sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, variant_sim_id)
        os.makedirs(variant_sim_dir, exist_ok=True)

        # Copy persona profiles to variant dir
        profiles_dst = os.path.join(variant_sim_dir, "twitter_profiles.csv")
        shutil.copy2(profiles_src, profiles_dst)

        # Read parent config for agent list
        parent_config_path = os.path.join(parent_sim_dir, "simulation_config.json")
        agent_configs = []
        if os.path.exists(parent_config_path):
            with open(parent_config_path, "r", encoding="utf-8") as f:
                parent_config = json.load(f)
            raw_agents = parent_config.get("agent_configs", [])
            agent_configs = [
                {
                    "agent_id": a.get("agent_id", a.get("user_id")),
                    "activity_level": a.get("activity_level", 0.7),
                }
                for a in raw_agents
                if a.get("agent_id", a.get("user_id")) is not None
            ]

        # Write variant simulation_config.json
        variant_config = {
            "simulation_id": variant_sim_id,
            "variant_id": variant_id,
            "channel": channel,
            "num_rounds": num_rounds,
            "brand_agent_id": 0,
            "campaign_content": campaign_content,
            "agent_configs": agent_configs,
            "channel_def": {
                "key": channel_def.key,
                "kind": channel_def.kind,
                "available_actions": channel_def.available_actions,
                "action_weights": channel_def.action_weights,
                "funnel_map": channel_def.funnel_map,
                "mechanics": channel_def.mechanics,
            },
        }
        variant_config_path = os.path.join(variant_sim_dir, "simulation_config.json")
        with open(variant_config_path, "w", encoding="utf-8") as f:
            json.dump(variant_config, f, indent=2, ensure_ascii=False)

        # Launch via SimulationRunner (platform="channel" -> run_channel_simulation.py).
        # Pass max_rounds so the runner's total_rounds tracks correctly (the variant
        # config has no time_config key, so without this it defaults to 144 rounds).
        state = SimulationRunner.start_simulation(
            simulation_id=variant_sim_id,
            platform="channel",
            max_rounds=num_rounds,
        )

        logger.info(
            f"Variant simulation launched: variant_sim_id={variant_sim_id}, "
            f"channel={channel}, pid={state.process_pid}"
        )

        # Record ownership + a campaign-history row, matching ab_test's pattern —
        # without this, a variant launched through this endpoint runs for real
        # but never shows up in campaign history/reports, since those are all
        # read from the campaigns/campaign_variants tables, not the filesystem.
        try:
            parent_sim = SimulationRecord.query.filter_by(sim_key=simulation_id).first()
            campaign_record = CampaignRecord(
                user_id=g.current_user.id,
                brand_brief_id=parent_sim.brand_brief_id if parent_sim else None,
                campaign_ref=variant_sim_id,
            )
            db.session.add(campaign_record)
            db.session.flush()
            db.session.add(CampaignVariantRecord(
                campaign_id=campaign_record.id,
                variant_ref=variant_id,
                channel=channel,
                status=state.runner_status,
            ))
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            logger.exception(f"Could not record campaign history for {variant_sim_id}: {db_err}")

        return jsonify({
            "success": True,
            "data": {
                "variant_sim_id": variant_sim_id,
                "simulation_dir": variant_sim_dir,
                "runner_status": state.runner_status,
                "process_pid": state.process_pid,
            }
        })

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"launch_variant failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500



@simulation_bp.route('/variant_status/<variant_sim_id>', methods=['GET'])
def variant_status(variant_sim_id: str):
    """Poll status of a running variant simulation.

    Returns env_status.json contents plus the runner state.

    Response:
    {
        "success": true,
        "data": {
            "runner_status": "running|completed|failed",
            "env_status": {...},
            "actions_count": 42
        }
    }
    """
    try:
        sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, variant_sim_id)
        if not os.path.isdir(sim_dir):
            return jsonify({
                "success": False,
                "error": f"Variant simulation not found: {variant_sim_id}"
            }), 404

        # Runner state
        state = SimulationRunner.get_run_state(variant_sim_id)
        runner_status = state.runner_status if state else "unknown"

        # Script-written status file
        env_status = {}
        env_status_path = os.path.join(sim_dir, "env_status.json")
        if os.path.exists(env_status_path):
            with open(env_status_path, "r", encoding="utf-8") as f:
                env_status = json.load(f)

        # Count exported agent actions (exclude sentinel lines)
        actions_count = 0
        actions_path = os.path.join(sim_dir, "actions.jsonl")
        if os.path.exists(actions_path):
            with open(actions_path, "r", encoding="utf-8") as f:
                actions_count = sum(
                    1 for line in f
                    if line.strip() and '"event_type"' not in line
                )

        return jsonify({
            "success": True,
            "data": {
                "variant_sim_id": variant_sim_id,
                "runner_status": runner_status,
                "env_status": env_status,
                "actions_count": actions_count,
            }
        })

    except Exception as e:
        logger.error(f"variant_status failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Phase 3 — A/B Testing & Campaign Variables ==============



@simulation_bp.route('/ab_test', methods=['POST'])
def start_ab_test():
    """Start a multi-variant A/B simulation.

    Builds a Campaign object from the request, launches all variants via
    VariantRunner (each gets its own subprocess), and persists the campaign
    so ab_status can poll it.

    Request body:
    {
        "simulation_id": "sim_xxxx",   // parent sim that ran /prepare
        "brand_name": "FreshBrew Coffee",
        "campaign_goal": "Drive trial purchase",
        "variants": [
            {
                "variant_name": "Video on Instagram",
                "channel": "instagram",
                "target_segment": "",
                "max_rounds": 10,
                "content": {
                    "format": "VideoAd",
                    "headline": "Zero Sugar. Zero Wait.",
                    "body": "Ready in 30 seconds.",
                    "cta": "Try it — 20% off",
                    "visual_desc": "Fast-paced montage",
                    "tone": "playful"
                }
            }
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "campaign_id": "...",
            "variants": [{"variant_id": "...", "variant_sim_id": "...", "status": "running"}]
        }
    }
    """
    from ..models.campaign import Campaign, CampaignVariant, CampaignContent
    from ..services.business_context import OBJECTIVES
    from ..services.channel_registry import get_channel
    from ..services.variant_runner import VariantRunner

    try:
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id")
        if not simulation_id:
            return jsonify({"success": False, "error": t("api.requireSimulationId")}), 400

        objective = data.get("objective") or ""
        if objective and objective not in OBJECTIVES:
            return jsonify({"success": False, "error": f"objective must be one of {OBJECTIVES}"}), 400

        variants_data = data.get("variants", [])
        if not (1 <= len(variants_data) <= 6):
            return jsonify({
                "success": False,
                "error": f"A campaign must have between 1 and 6 variants (got {len(variants_data)})",
            }), 400

        # Validate every variant's channel+format against the registry before
        # launching anything — fail fast on bad input rather than partially
        # launching subprocesses.
        format_errors = []
        for i, v_data in enumerate(variants_data):
            channel_key = v_data.get("channel", "")
            channel_def = get_channel(g.current_user.id, channel_key)
            if channel_def is None:
                format_errors.append(f"variant {i + 1}: unknown channel '{channel_key}'")
                continue
            fmt = (v_data.get("content") or {}).get("format", "")
            if channel_def.formats and fmt.lower() not in {f.lower() for f in channel_def.formats}:
                format_errors.append(
                    f"variant {i + 1}: format '{fmt}' is not valid for channel "
                    f"'{channel_key}' (valid formats: {', '.join(channel_def.formats)})"
                )
        if format_errors:
            return jsonify({"success": False, "error": "Invalid variant(s)", "details": format_errors}), 400

        # Build Campaign object
        campaign = Campaign(
            simulation_id=simulation_id,
            brand_name=data.get("brand_name", ""),
            campaign_goal=data.get("campaign_goal", ""),
            objective=objective,
        )

        for v_data in variants_data:
            c = v_data.get("content", {})
            content = CampaignContent(
                format=c.get("format", "CarouselPost"),
                headline=c.get("headline", ""),
                body=c.get("body", ""),
                cta=c.get("cta", ""),
                visual_desc=c.get("visual_desc", ""),
                email_subject=c.get("email_subject", ""),
                tone=c.get("tone", "neutral"),
            )
            variant = CampaignVariant(
                variant_name=v_data.get("variant_name", "Variant"),
                channel=v_data.get("channel", "instagram"),
                target_segment=v_data.get("target_segment", ""),
                # 0 = "not specified" -> VariantRunner falls back to the channel's own default
                max_rounds=int(v_data.get("max_rounds") or 0),
                content=content,
                provenance=v_data.get("provenance") or "user",
                rationale=v_data.get("rationale"),
                hypothesis=v_data.get("hypothesis"),
            )
            campaign.variants.append(variant)

        # Iteration lineage (Phase 3): set when this campaign was launched from
        # an Insight redesign proposal applied through the Designer flow.
        parent_campaign_id = data.get("parent_campaign_id")
        parent_campaign = None
        if parent_campaign_id:
            import uuid as _uuid
            try:
                parent_campaign = CampaignRecord.query.filter_by(
                    id=_uuid.UUID(str(parent_campaign_id)), user_id=g.current_user.id
                ).first()
            except ValueError:
                parent_campaign = None
            if not parent_campaign:
                return jsonify({"success": False, "error": "parent_campaign_id not found"}), 404
        iteration = (parent_campaign.iteration + 1) if parent_campaign else int(data.get("iteration") or 1)

        # Launch all variants
        runner = VariantRunner()
        campaign = runner.launch_all(campaign, user_id=g.current_user.id)

        # Persist campaign for polling
        _save_campaign(campaign)

        # Record ownership so ab_status/campaign_recommendations/etc. can be gated.
        parent_sim = SimulationRecord.query.filter_by(sim_key=simulation_id).first()
        campaign_record = CampaignRecord(
            user_id=g.current_user.id,
            brand_brief_id=parent_sim.brand_brief_id if parent_sim else None,
            campaign_ref=campaign.campaign_id,
            brand_name=campaign.brand_name,
            campaign_goal=campaign.campaign_goal,
            objective=campaign.objective or None,
            parent_campaign_id=parent_campaign.id if parent_campaign else None,
            iteration=iteration,
        )
        db.session.add(campaign_record)
        db.session.flush()
        for v in campaign.variants:
            db.session.add(CampaignVariantRecord(
                campaign_id=campaign_record.id,
                variant_ref=v.variant_id,
                variant_name=v.variant_name,
                channel=v.channel,
                content=asdict(v.content) if v.content else None,
                target_segment=v.target_segment,
                status=v.status,
                provenance=v.provenance,
                rationale=v.rationale,
                hypothesis=v.hypothesis,
            ))
        db.session.commit()

        logger.info(
            f"A/B test launched: campaign_id={campaign.campaign_id}, "
            f"{len(campaign.variants)} variants"
        )

        return jsonify({
            "success": True,
            "data": {
                "campaign_id": campaign.campaign_id,
                "variants": [
                    {
                        "variant_id": v.variant_id,
                        "variant_name": v.variant_name,
                        "channel": v.channel,
                        "variant_sim_id": v.variant_sim_id,
                        "status": v.status,
                        "error": v.error,
                    }
                    for v in campaign.variants
                ],
            }
        })

    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"start_ab_test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500



@simulation_bp.route('/ab_status/<campaign_id>', methods=['GET'])
def ab_status(campaign_id: str):
    """Poll the status of all variants in a campaign.

    Response:
    {
        "success": true,
        "data": {
            "campaign_id": "...",
            "total_variants": 3,
            "completed": 2,
            "failed": 0,
            "all_done": false,
            "variants": [
                {
                    "variant_id": "...",
                    "variant_name": "...",
                    "channel": "instagram",
                    "variant_sim_id": "...",
                    "runner_status": "running",
                    "env_status": {"status": "running", "timestamp": "..."},
                    "actions_count": 47
                }
            ]
        }
    }
    """
    from ..services.variant_runner import VariantRunner

    try:
        campaign = _load_campaign(campaign_id)
        if campaign is None:
            return jsonify({"success": False, "error": f"Campaign not found: {campaign_id}"}), 404

        runner = VariantRunner()
        status = runner.get_campaign_status(campaign)

        return jsonify({"success": True, "data": status})

    except Exception as e:
        logger.error(f"ab_status failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500



@simulation_bp.route('/campaign_recommendations', methods=['POST'])
def generate_campaign_recommendations():
    """
    Score all simulation variants and generate a recommendation report.

    Request:
        { "campaign_id": "...", "graph_id": "..." }
        graph_id is optional — used to enrich recommendations with brand context.

    Returns:
        { "success": true, "data": { "task_id": "..." } }
    """
    import threading
    from ..models.task import TaskManager, TaskStatus
    from ..services.variant_scorer import VariantScorer
    from ..services.campaign_report_agent import CampaignReportAgent

    try:
        data = request.get_json() or {}
        campaign_id = data.get("campaign_id")
        graph_id = data.get("graph_id")

        if not campaign_id:
            return jsonify({"success": False, "error": "campaign_id is required"}), 400

        # Load as raw dict — _save_campaign wraps a Campaign object and can't store
        # extra keys like campaign_report; use the JSON file directly instead.
        campaign_path = os.path.join(_campaigns_dir(), f"{campaign_id}.json")
        if not os.path.exists(campaign_path):
            return jsonify({"success": False, "error": f"Campaign {campaign_id} not found"}), 404
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign_dict = json.load(f)

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="campaign_report",
            metadata={"campaign_id": campaign_id},
            user_id=g.current_user.id,
        )

        def _run():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="Scoring simulation variants...",
                )
                scorer = VariantScorer()
                scored = scorer.score_campaign(campaign_dict)

                if not scored:
                    task_manager.fail_task(task_id, "No completed variants with action logs found.")
                    return

                task_manager.update_task(
                    task_id,
                    progress=50,
                    message=f"Scored {len(scored)} variants. Generating recommendations...",
                )

                from ..services.kg import KGClient as _KGClient
                zep_client = _KGClient(data_dir=Config.KG_DATA_DIR) if graph_id else None

                agent = CampaignReportAgent(
                    scored_variants=scored,
                    zep_client=zep_client,
                    graph_id=graph_id,
                )
                result = agent.generate({
                    "brand_name":    campaign_dict.get("brand_name", ""),
                    "campaign_goal": campaign_dict.get("campaign_goal", ""),
                })

                # Persist report back into campaign JSON directly (bypasses Campaign.to_dict()
                # which only serialises declared dataclass fields and would drop campaign_report)
                campaign_dict["campaign_report"] = result
                with open(campaign_path, "w", encoding="utf-8") as f:
                    json.dump(campaign_dict, f, indent=2, ensure_ascii=False)

                task_manager.complete_task(
                    task_id,
                    result={"campaign_id": campaign_id, "report_saved": True},
                )

            except Exception as e:
                logger.error(f"Campaign recommendation generation failed: {e}")
                task_manager.fail_task(task_id, str(e))

        threading.Thread(target=_run, daemon=True).start()

        return jsonify({"success": True, "data": {"task_id": task_id}})

    except Exception as e:
        logger.error(f"campaign_recommendations endpoint failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500



@simulation_bp.route('/campaign_report/<campaign_id>', methods=['GET'])
def get_campaign_report(campaign_id: str):
    """
    Retrieve the generated campaign recommendation report.

    Returns the full report dict saved inside the campaign JSON, plus
    pre-computed scored_variants for the UI ranking table.

    Query params:
        format=markdown  — return only the report_text as plain text
    """
    try:
        campaign_path = os.path.join(_campaigns_dir(), f"{campaign_id}.json")
        if not os.path.exists(campaign_path):
            return jsonify({"success": False, "error": f"Campaign {campaign_id} not found"}), 404
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign_dict = json.load(f)

        report = campaign_dict.get("campaign_report")
        if not report:
            return jsonify({
                "success": False,
                "error": "No report generated yet. Call POST /campaign_recommendations first.",
            }), 404

        fmt = request.args.get("format", "json")
        if fmt == "markdown":
            from flask import Response
            return Response(
                report.get("report_text", "No report text."),
                mimetype="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=campaign_report_{campaign_id}.md"
                },
            )

        return jsonify({"success": True, "data": report})

    except Exception as e:
        logger.error(f"get_campaign_report failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/campaign_lineage/<campaign_id>', methods=['GET'])
def get_campaign_lineage(campaign_id: str):
    """Full iteration chain (ancestors + descendants) for this campaign, oldest first."""
    from ..services.campaign_lineage import get_lineage_chain

    record = CampaignRecord.query.filter_by(campaign_ref=campaign_id, user_id=g.current_user.id).first()
    if not record:
        return jsonify({"success": False, "error": "Campaign not found"}), 404
    return jsonify({"success": True, "data": get_lineage_chain(record)})



@simulation_bp.route('/campaigns', methods=['GET'])
def list_campaigns():
    """List all past and active A/B campaigns for the history dashboard.

    Returns campaigns sorted newest-first, each enriched with a derived
    `overall_status` (pending / running / completed / failed) computed from
    variant statuses.

    Query params:
        limit (int, default 50) — max campaigns to return
    """
    try:
        limit = int(request.args.get("limit", 50))
        campaigns_dir = _campaigns_dir()

        # Campaign JSON files carry no owner field of their own — ownership is
        # tracked in the campaigns table (campaign_ref -> user_id), same as
        # everywhere else. Legacy files with no matching row are excluded
        # rather than shown to everyone.
        owned_refs = {
            rec.campaign_ref
            for rec in CampaignRecord.query.filter_by(user_id=g.current_user.id).all()
            if rec.campaign_ref
        }

        items = []
        for fname in os.listdir(campaigns_dir):
            if not fname.endswith(".json"):
                continue
            campaign_ref = fname[:-len(".json")]
            if campaign_ref not in owned_refs:
                continue
            path = os.path.join(campaigns_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            variants = data.get("variants", [])
            statuses = [v.get("status", "pending") for v in variants]

            if all(s == "completed" for s in statuses):
                overall_status = "completed"
            elif any(s == "failed" for s in statuses):
                overall_status = "failed"
            elif any(s == "running" for s in statuses):
                overall_status = "running"
            else:
                overall_status = "pending"

            has_report = bool(data.get("campaign_report"))

            items.append({
                "campaign_id":   data.get("campaign_id"),
                "simulation_id": data.get("simulation_id"),
                "brand_name":    data.get("brand_name", ""),
                "campaign_goal": data.get("campaign_goal", ""),
                "created_at":    data.get("created_at"),
                "variant_count": len(variants),
                "variants":      [
                    {
                        "variant_id":   v.get("variant_id"),
                        "variant_name": v.get("variant_name"),
                        "channel":      v.get("channel"),
                        "status":       v.get("status", "pending"),
                    }
                    for v in variants
                ],
                "overall_status": overall_status,
                "has_report":    has_report,
            })

        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        items = items[:limit]

        return jsonify({"success": True, "data": items, "total": len(items)})

    except Exception as e:
        logger.error(f"list_campaigns failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

