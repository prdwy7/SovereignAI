//! Local validation oracle. Includes pinned source in place; no upstream source is vendored.
#![allow(dead_code, unused_imports)]

mod types { include!(concat!(env!("SILICATE_SOURCE_ROOT"), "/crates/silicate-core/src/types.rs")); }
mod canonical { include!(concat!(env!("SILICATE_SOURCE_ROOT"), "/crates/silicate-core/src/canonical.rs")); }
mod identity { include!(concat!(env!("SILICATE_SOURCE_ROOT"), "/crates/silicate-core/src/identity.rs")); }
mod object { include!(concat!(env!("SILICATE_SOURCE_ROOT"), "/crates/silicate-core/src/object.rs")); }
mod relation { include!(concat!(env!("SILICATE_SOURCE_ROOT"), "/crates/silicate-core/src/relation.rs")); }
mod derivation { include!(concat!(env!("SILICATE_SOURCE_ROOT"), "/crates/silicate-core/src/derivation.rs")); }

use canonical::{CanonicalDecode, CanonicalEncode};
use derivation::*;
use object::Object;
use relation::Relation;
use types::*;

fn hex(bytes: &[u8]) -> String { bytes.iter().map(|b| format!("{b:02x}")).collect() }

fn main() {
    let suite = identity::IdentitySuite::V1Sha256;
    for (name, payload) in [("object_empty", vec![]), ("object_scalar_a", vec![0, 0, 0, 65])] {
        let obj = Object { id: ObjectId([0;32]), object_type: ObjectTypeId([1;32]),
            definition: DefinitionId([2;32]), schema: SchemaId([3;32]), payload };
        let bytes = obj.canonical_bytes();
        let (decoded, consumed) = Object::from_canonical_bytes(&bytes).unwrap();
        assert_eq!(consumed, bytes.len());
        assert_eq!(decoded.canonical_bytes(), bytes);
        println!("{name}|object|{}|{}", hex(&bytes), hex(&identity::compute_object_id(suite, &obj).0));
    }
    for (name, ordering) in [("relation_none", None), ("relation_zero", Some(0)), ("relation_max", Some(u64::MAX))] {
        let rel = Relation { id: RelationId([0;32]), source: ObjectId([4;32]),
            relation_type: RelationTypeId([5;32]), target: ObjectId([6;32]), ordering, context: vec![7,8] };
        let bytes = rel.canonical_bytes();
        let (decoded, consumed) = Relation::from_canonical_bytes(&bytes).unwrap();
        assert_eq!(consumed, bytes.len());
        assert_eq!(decoded.canonical_bytes(), bytes);
        println!("{name}|relation|{}|{}", hex(&bytes), hex(&identity::compute_relation_id(suite, &rel).0));
    }
    for (name, execution_class) in [("derivation_deterministic", ExecutionClass::Deterministic),
                                  ("derivation_attested", ExecutionClass::Attested)] {
        let dev = Derivation { id: DerivationId([0;32]), execution_class,
            inputs: vec![DerivationInput::Object(ObjectId([1;32])), DerivationInput::Relation(RelationId([2;32])), DerivationInput::Object(ObjectId([1;32]))],
            operation: OperationId([3;32]), rule: RuleId([4;32]), rule_version: 1,
            parameters: vec![0,1], outputs: vec![DerivationOutput::Object(ObjectId([5;32])), DerivationOutput::Relation(RelationId([6;32]))] };
        let bytes = dev.canonical_bytes();
        let (decoded, consumed) = Derivation::from_canonical_bytes(&bytes).unwrap();
        assert_eq!(consumed, bytes.len());
        assert_eq!(decoded.canonical_bytes(), bytes);
        println!("{name}|derivation|{}|{}", hex(&bytes), hex(&identity::compute_derivation_id(suite, &dev).0));
    }
}
