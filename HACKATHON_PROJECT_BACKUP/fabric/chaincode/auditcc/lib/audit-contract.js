'use strict';

const { Contract } = require('fabric-contract-api');

const DOC_TYPE = 'auditRecord';

function recordKey(eventId) {
  return `EVENT:${eventId}`;
}

function historyKey(kind, resourceId, eventId) {
  return `HIST:${kind}:${resourceId}:${eventId}`;
}

function toIso(timestamp) {
  if (!timestamp) {
    return null;
  }
  const secondsRaw = timestamp.seconds;
  const seconds = Number(
    secondsRaw && typeof secondsRaw === 'object' && secondsRaw.low !== undefined
      ? secondsRaw.low
      : secondsRaw
  );
  const nanos = Number(timestamp.nanos || 0);
  return new Date(seconds * 1000 + nanos / 1e6).toISOString();
}

class AuditContract extends Contract {
  constructor() {
    super('auditcc');
  }

  _now(timestamp) {
    return timestamp || new Date().toISOString();
  }

  async _put(ctx, record) {
    const key = recordKey(record.eventId);
    const existing = await ctx.stub.getState(key);
    if (existing && existing.length > 0) {
      throw new Error(`Audit event ${record.eventId} is already anchored`);
    }
    record.docType = DOC_TYPE;
    record.txId = ctx.stub.getTxID();
    await ctx.stub.putState(key, Buffer.from(JSON.stringify(record)));
    await ctx.stub.putState(
      historyKey(record.kind, record.resourceId || record.eventId, record.eventId),
      Buffer.from(JSON.stringify({ eventId: record.eventId, kind: record.kind }))
    );
    return record;
  }

  /**
   * Anchor a generic critical audit event hash.
   * Only the SHA-256 hash is stored — never the raw event payload.
   */
  async recordAuditEvent(ctx, eventId, hash, resourceType, timestamp) {
    if (!eventId || !hash || !resourceType) {
      throw new Error('eventId, hash, and resourceType are required');
    }
    return this._put(ctx, {
      eventId,
      kind: 'audit',
      hash,
      resourceType,
      resourceId: eventId,
      action: 'audit.record',
      timestamp: this._now(timestamp),
    });
  }

  /**
   * Anchor a firewall / approval change hash.
   */
  async recordFirewallChange(ctx, changeId, hash, firewallId, timestamp) {
    if (!changeId || !hash || !firewallId) {
      throw new Error('changeId, hash, and firewallId are required');
    }
    return this._put(ctx, {
      eventId: changeId,
      kind: 'firewall',
      hash,
      resourceType: 'firewall',
      resourceId: firewallId,
      action: 'firewall.change',
      timestamp: this._now(timestamp),
    });
  }

  /**
   * Anchor a server inventory change hash.
   */
  async recordServerChange(ctx, eventId, hash, serverId, timestamp) {
    if (!eventId || !hash || !serverId) {
      throw new Error('eventId, hash, and serverId are required');
    }
    return this._put(ctx, {
      eventId,
      kind: 'server',
      hash,
      resourceType: 'server',
      resourceId: serverId,
      action: 'server.change',
      timestamp: this._now(timestamp),
    });
  }

  /**
   * Return the current record plus ledger history for an event or resource id.
   */
  async getAuditHistory(ctx, id) {
    if (!id) {
      throw new Error('id is required');
    }
    const direct = await ctx.stub.getState(recordKey(id));
    const records = [];
    if (direct && direct.length > 0) {
      const current = JSON.parse(direct.toString());
      const iterator = await ctx.stub.getHistoryForKey(recordKey(id));
      const history = [];
      let result = await iterator.next();
      while (!result.done) {
        const value = result.value;
        history.push({
          txId: value.txId,
          timestamp: toIso(value.timestamp),
          isDelete: Boolean(value.isDelete),
          record: value.value && value.value.length ? JSON.parse(value.value.toString()) : null,
        });
        result = await iterator.next();
      }
      await iterator.close();
      return { current, history };
    }

    for (const kind of ['audit', 'firewall', 'server']) {
      const prefix = `HIST:${kind}:${id}:`;
      const rng = await ctx.stub.getStateByRange(prefix, `${prefix}\uffff`);
      let result = await rng.next();
      while (!result.done) {
        const pointer = JSON.parse(result.value.value.toString());
        const body = await ctx.stub.getState(recordKey(pointer.eventId));
        if (body && body.length > 0) {
          records.push(JSON.parse(body.toString()));
        }
        result = await rng.next();
      }
      await rng.close();
    }
    return { current: null, matches: records };
  }

  /**
   * Compare a locally computed SHA-256 hash with the on-chain hash.
   */
  async verifyIntegrity(ctx, eventId, hash) {
    if (!eventId || !hash) {
      throw new Error('eventId and hash are required');
    }
    const raw = await ctx.stub.getState(recordKey(eventId));
    if (!raw || raw.length === 0) {
      return { eventId, anchored: false, matches: false, reason: 'not_found' };
    }
    const record = JSON.parse(raw.toString());
    const matches = record.hash === hash;
    return {
      eventId,
      anchored: true,
      matches,
      onChainHash: record.hash,
      txId: record.txId,
      kind: record.kind,
    };
  }
}

module.exports = AuditContract;
