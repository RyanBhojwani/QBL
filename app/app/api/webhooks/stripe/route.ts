import { clerkClient } from "@clerk/nextjs/server";
import { stripe, PRICE_TO_TIER } from "@/lib/stripe";
import Stripe from "stripe";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get("stripe-signature");

  if (!sig) {
    return new Response("No signature", { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    console.error("Webhook signature verification failed:", err);
    return new Response("Invalid signature", { status: 400 });
  }

  const client = await clerkClient();

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      if (!session.subscription) break;

      // Retrieve subscription — metadata and price ID live there
      const subscription = await stripe.subscriptions.retrieve(session.subscription as string);
      const clerkUserId = subscription.metadata?.clerkUserId;
      const priceId = subscription.items.data[0]?.price.id;
      const tier = PRICE_TO_TIER[priceId];

      if (clerkUserId && tier) {
        await client.users.updateUserMetadata(clerkUserId, {
          publicMetadata: { tier },
        });
      }
      break;
    }

    case "customer.subscription.updated": {
      const subscription = event.data.object as Stripe.Subscription;
      const clerkUserId = subscription.metadata?.clerkUserId;
      if (!clerkUserId) break;

      const priceId = subscription.items.data[0]?.price.id;
      const tier = PRICE_TO_TIER[priceId];

      if (tier && subscription.status === "active") {
        await client.users.updateUserMetadata(clerkUserId, {
          publicMetadata: { tier },
        });
      }
      break;
    }

    case "customer.subscription.deleted": {
      const subscription = event.data.object as Stripe.Subscription;
      const clerkUserId = subscription.metadata?.clerkUserId;
      if (!clerkUserId) break;

      await client.users.updateUserMetadata(clerkUserId, {
        publicMetadata: { tier: null },
      });
      break;
    }
  }

  return new Response("ok", { status: 200 });
}
