import Stripe from "stripe";

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2026-04-22.dahlia",
});

export const PRICE_TO_TIER: Record<string, "basic" | "premium" | "vip"> = {
  [process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC!]: "basic",
  [process.env.NEXT_PUBLIC_STRIPE_PRICE_PREMIUM!]: "premium",
  [process.env.NEXT_PUBLIC_STRIPE_PRICE_VIP!]: "vip",
};
